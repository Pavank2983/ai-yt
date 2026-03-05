import os
import json
import logging
import traceback
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.video_job import VideoJob, JobStatus
from app.models.video import Video

from app.utils import asset_paths

# ✅ Cost Intelligence
from app.services.cost_service import (
    calculate_actual_cost,
    update_video_total_cost,
)

# ✅ Failure Intelligence
from app.services.provider_health_service import (
    is_provider_healthy,
    record_provider_failure,
    record_provider_success,
)

# Provider imports
from app.services.providers import (
    minimax_service,
    veo_service,
    sora_service,
    kling_service,
    runway_service,
    siliconflow_service,
)

logger = logging.getLogger("scheduler_logger")

# ---------------------------------------------------------
# PROVIDER REGISTRY
# ---------------------------------------------------------
PROVIDERS = {
    "MINIMAX": minimax_service,
    "VEO": veo_service,
    "SORA": sora_service,
    "KLING": kling_service,
    "RUNWAY": runway_service,
    "SILICONFLOW": siliconflow_service,
}

# ---------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------
def to_json(data):
    try:
        return json.dumps(data, ensure_ascii=False)
    except Exception:
        return "{}"


def from_json(data):
    try:
        return json.loads(data) if isinstance(data, str) else data
    except Exception:
        return {}


# ---------------------------------------------------------
# 1️⃣ SUBMIT QUEUED JOB
# ---------------------------------------------------------
def submit_job_to_provider(job_id: int, db: Session = None) -> dict:
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job:
            raise Exception(f"VideoJob {job_id} not found")

        video = db.query(Video).filter(Video.id == job.video_id).first()
        if not video:
            raise Exception(f"Video {job.video_id} not found")

        provider = (job.provider or "").upper().strip()

        # ✅ Provider Health Check
        if not is_provider_healthy(db, provider):
            logger.warning(
                f"🚫 Provider {provider} is in cooldown. Skipping submission."
            )
            job.error_log = "Provider in cooldown (Failure Intelligence)"
            job.updated_at = datetime.now(timezone.utc)

            if own_session:
                db.commit()

            return {"status": "cooldown"}

        provider_mod = PROVIDERS.get(provider)
        if not provider_mod:
            raise Exception(f"Provider '{provider}' not supported")

        logger.info(f"🧠 Submitting Job {job.id} to provider: {provider}")

        submit_result = provider_mod.submit(job, video)

        # 🔥 Validate provider submission
        if submit_result.get("status") == "failed":
            error_msg = submit_result.get("error", "Provider submission failed")
            raise Exception(error_msg)

        task_id = submit_result.get("task_id")
        if not task_id:
            raise Exception(
                f"Provider {provider} did not return task_id. Payload: {submit_result}"
            )

        job.task_id = task_id

        if submit_result.get("meta"):
            job.meta = to_json(submit_result["meta"])

        # --------------------------------------------------
        # Instant providers
        # --------------------------------------------------
        if submit_result.get("file_path"):
            job.status = JobStatus.success
            job.local_path = submit_result["file_path"]
            job.completed_at = datetime.now(timezone.utc)
            job.updated_at = datetime.now(timezone.utc)

            # ✅ Record success
            record_provider_success(db, provider)

            # ✅ COST
            actual_cost = calculate_actual_cost(
                job=job,
                duration_seconds=video.video_length,
            )
            job.actual_cost = Decimal(actual_cost)

            if own_session:
                db.commit()
                update_video_total_cost(db, job.video_id)

            return {
                "status": "success",
                "file_path": submit_result["file_path"],
            }

        if own_session:
            db.commit()

        return {"status": "queued", "task_id": job.task_id}

    except Exception as e:
        if own_session:
            db.rollback()

        logger.error(f"❌ Error submitting job {job_id}: {e}")
        logger.debug(traceback.format_exc())
        raise

    finally:
        if own_session:
            db.close()


# ---------------------------------------------------------
# 2️⃣ PROCESS RUNNING JOB (POLL → RETRIEVE → DOWNLOAD)
# ---------------------------------------------------------
def process_running_job(job_id: int, db: Session = None) -> dict:
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job:
            raise Exception(f"VideoJob {job_id} not found")

        video = db.query(Video).filter(Video.id == job.video_id).first()
        if not video:
            raise Exception(f"Video {job.video_id} not found")

        provider = (job.provider or "").upper().strip()
        provider_mod = PROVIDERS.get(provider)
        if not provider_mod:
            raise Exception(f"Provider '{provider}' not supported")

        if not job.task_id:
            raise Exception(f"Job {job.id} has no task_id")

        logger.info(
            f"🔍 Polling provider={provider} | job_id={job.id} | task_id={job.task_id}"
        )

        poll_result = provider_mod.poll(job)

        # 🔎 LOG RAW PROVIDER RESPONSE (VERY IMPORTANT)
        logger.info(
            f"📡 Poll result | provider={provider} | job_id={job.id} | "
            f"status={poll_result.get('status')} | payload={poll_result}"
        )

        if poll_result.get("meta"):
            job.meta = to_json(poll_result["meta"])

        # -----------------------------
        # PROCESSING
        # -----------------------------
        if poll_result["status"] == "processing":
            logger.info(
                f"⏳ Still processing | provider={provider} | job_id={job.id}"
            )

            job.attempts += 1
            job.updated_at = datetime.now(timezone.utc)

            if own_session:
                db.commit()

            return {"status": "processing"}

        # -----------------------------
        # FAILED
        # -----------------------------
        if poll_result["status"] == "failed":
            error_msg = poll_result.get(
                "error",
                poll_result.get("message", "Provider polling failed"),
            )

            record_provider_failure(db, provider)
            logger.error(
                f"❌ Provider FAILED | provider={provider} | job_id={job.id} | "
                f"task_id={job.task_id} | error={error_msg}"
            )

            job.error_log = error_msg
            job.updated_at = datetime.now(timezone.utc)

            if own_session:
                db.commit()

            return {"status": "failed", "error": error_msg}

        # -----------------------------
        # SUCCESS
        # -----------------------------
        record_provider_success(db, provider)
        logger.info(
            f"✅ Provider SUCCESS | provider={provider} | job_id={job.id} | "
            f"task_id={job.task_id}"
        )

        # -----------------------------
        # RETRIEVE FILE INFO
        # -----------------------------
        if provider == "MINIMAX":
            file_id = poll_result.get("file_id")
            if not file_id:
                raise Exception("MiniMax success but no file_id")

            logger.info(
                f"📥 Retrieving MiniMax file | job_id={job.id} | file_id={file_id}"
            )

            job.file_id = file_id

            if own_session:
                db.commit()

            retrieve_result = provider_mod.retrieve(file_id)
            download_url = retrieve_result["download_url"]

        elif provider == "SILICONFLOW":
            logger.info(
                f"📥 Retrieving SiliconFlow file | job_id={job.id} | task_id={job.task_id}"
            )

            retrieve_result = provider_mod.retrieve(job)
            download_url = retrieve_result["download_url"]

        else:
            raise Exception(f"Retrieve not implemented for {provider}")

        # -----------------------------
        # SCENE OUTPUT PATH
        # -----------------------------
        script_id = job.script_id
        scene_index = job.scene_index

        scene_dir = asset_paths.scene_dir(script_id, scene_index)
        os.makedirs(scene_dir, exist_ok=True)

        final_path = os.path.join(scene_dir, "output.mp4")

        logger.info(
            f"⬇️ Downloading video | provider={provider} | job_id={job.id} | "
            f"url={download_url} | output={final_path}"
        )

        provider_mod.download(download_url, final_path)

        # -----------------------------
        # UPDATE JOB
        # -----------------------------
        job.local_path = final_path
        job.video_url = download_url
        job.status = JobStatus.success
        job.completed_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)

        actual_cost = calculate_actual_cost(
            job=job,
            duration_seconds=video.video_length,
        )
        job.actual_cost = Decimal(actual_cost)

        if own_session:
            db.commit()
            logger.info(
                f"🎉 Scene completed | job_id={job.id} | scene={scene_index} | "
                f"path={final_path}"
            )
            update_video_total_cost(db, job.video_id)

        return {"status": "success", "file_path": final_path}

    except Exception as e:
        if own_session:
            db.rollback()

        logger.error(
            f"❌ Exception during polling | job_id={job_id} | error={e}",
            exc_info=True,
        )

        return {"status": "failed", "error": str(e)}

    finally:
        if own_session:
            db.close()