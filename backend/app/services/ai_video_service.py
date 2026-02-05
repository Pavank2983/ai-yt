import os
import json
import logging
import traceback
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.video_job import VideoJob, JobStatus
from app.models.video import Video

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
def submit_job_to_provider(job_id: int) -> dict:
    db: Session = SessionLocal()

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

        logger.info(f"🧠 Submitting Job {job.id} to provider: {provider}")

        submit_result = provider_mod.submit(job, video)

        if submit_result.get("task_id"):
            job.task_id = submit_result["task_id"]

        if submit_result.get("meta"):
            job.meta = to_json(submit_result["meta"])

        # Instant success providers (DEV / local only)
        if submit_result.get("file_path"):
            job.status = JobStatus.success
            job.local_path = submit_result["file_path"]
            job.completed_at = datetime.now(timezone.utc)
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

            return {
                "status": "success",
                "file_path": submit_result["file_path"],
            }

        db.commit()
        return {"status": "queued", "task_id": job.task_id}

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error submitting job {job_id}: {e}")
        logger.debug(traceback.format_exc())
        raise

    finally:
        db.close()


# ---------------------------------------------------------
# 2️⃣ PROCESS RUNNING JOB (POLL → RETRIEVE → DOWNLOAD)
# ---------------------------------------------------------
def process_running_job(job_id: int) -> dict:
    db: Session = SessionLocal()

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

        logger.info(f"🔍 Polling provider {provider} for task_id={job.task_id} | file=Ai_Video_Service.py")

        poll_result = provider_mod.poll(job)

        if poll_result.get("meta"):
            job.meta = to_json(poll_result["meta"])

        # -----------------------------
        # PROCESSING
        # -----------------------------
        if poll_result["status"] == "processing":
            job.attempts += 1
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "processing"}

        # -----------------------------
        # FAILED
        # -----------------------------
        if poll_result["status"] == "failed":
            job.status = JobStatus.failed
            job.error_log = "Provider returned failure"
            job.completed_at = datetime.now(timezone.utc)
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "failed"}

        # -----------------------------
        # SUCCESS
        # -----------------------------
        logger.info(f"✅ Provider reports SUCCESS for job {job.id}")

        # -----------------------------
        # RETRIEVE FILE INFO (provider-specific)
        # -----------------------------
        if provider == "MINIMAX":
            file_id = poll_result.get("file_id")
            if not file_id:
                raise Exception("MiniMax success but no file_id")

            job.file_id = file_id
            db.commit()

            retrieve_result = provider_mod.retrieve(file_id)
            download_url = retrieve_result["download_url"]
            filename = retrieve_result.get("filename", f"{provider}_{file_id}.mp4")

        elif provider == "SILICONFLOW":
            retrieve_result = provider_mod.retrieve(job)
            download_url = retrieve_result["download_url"]
            filename = retrieve_result.get("filename", f"{provider}_{job.task_id}.mp4")

        else:
            raise Exception(f"Retrieve logic not implemented for {provider}")

        # -----------------------------
        # DOWNLOAD
        # -----------------------------
        final_path = f"assets/videos/{provider.lower()}_{job.task_id}.mp4"
        provider_mod.download(download_url, final_path)

        # -----------------------------
        # UPDATE VIDEO
        # -----------------------------
        video.file_url = final_path
        video.status = "uploaded"
        video.updated_at = datetime.now(timezone.utc)

        # -----------------------------
        # UPDATE JOB
        # -----------------------------
        job.local_path = final_path
        job.video_url = download_url
        job.status = JobStatus.success
        job.completed_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)

        db.commit()

        logger.info(f"🎉 Job {job.id} completed → {final_path}")

        return {"status": "success", "file_path": final_path}

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error processing running job {job_id}: {e}")
        logger.debug(traceback.format_exc())

        try:
            job.status = JobStatus.failed
            job.error_log = f"{type(e).__name__}: {str(e)}"
            job.updated_at = datetime.now(timezone.utc)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
        except Exception:
            db.rollback()

        return {"status": "failed", "error": str(e)}

    finally:
        db.close()
