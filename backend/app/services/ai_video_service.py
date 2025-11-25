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
    runway_service
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
    "RUNWAY": runway_service
}

# ---------------------------------------------------------
# Utility: Safe JSON encode for meta
# ---------------------------------------------------------
def to_json(data):
    try:
        return json.dumps(data, ensure_ascii=False)
    except:
        return "{}"

# ---------------------------------------------------------
# 1️⃣ SUBMIT QUEUED JOB TO PROVIDER
# ---------------------------------------------------------
def submit_job_to_provider(job_id: int) -> dict:
    """
    Called when job is in 'queued' state.
    Sends prompt/script to provider.
    Saves task_id, meta.
    """

    db = SessionLocal()

    try:
        job: VideoJob = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job:
            raise Exception(f"VideoJob {job_id} not found")

        video: Video = db.query(Video).filter(Video.id == job.video_id).first()
        if not video:
            raise Exception(f"Video {job.video_id} not found for job {job.id}")

        provider = job.provider.upper()
        provider_mod = PROVIDERS.get(provider)
        if not provider_mod:
            raise Exception(f"Provider '{provider}' not supported")

        logger.info(f"🧠 Submitting Job {job.id} to provider: {provider}")

        # Provider returns:
        # { "task_id": "...", "file_path": optional, "meta": {...} }
        submit_result = provider_mod.submit(job, video)

        # Save task_id
        if submit_result.get("task_id"):
            job.task_id = submit_result["task_id"]

        # Save meta (raw provider response)
        if submit_result.get("meta"):
            job.meta = to_json(submit_result["meta"])

        # If provider returned video instantly
        if submit_result.get("file_path"):
            final_path = submit_result["file_path"]
            video.file_url = final_path
            video.status = "uploaded"
            video.updated_at = datetime.now(timezone.utc)

            job.status = JobStatus.success
            job.local_path = final_path
            job.completed_at = datetime.now(timezone.utc)
            job.updated_at = datetime.now(timezone.utc)

            db.commit()

            return {
                "status": "success",
                "file_path": final_path,
                "meta": submit_result.get("meta", {})
            }

        # Else: queued provider (MiniMax)
        db.commit()

        return {
            "status": "queued",
            "task_id": job.task_id,
            "meta": submit_result.get("meta", {})
        }

    except Exception as e:
        logger.error(f"❌ Error submitting job {job_id}: {e}")
        logger.debug(traceback.format_exc())
        raise

    finally:
        db.close()


# ---------------------------------------------------------
# 2️⃣ PROCESS RUNNING JOBS (POLL, RETRIEVE, DOWNLOAD)
# ---------------------------------------------------------
def process_running_job(job_id: int) -> dict:
    """
    Called when job.status == running.
    Poll provider, retrieve file, download file, update DB.
    """

    db = SessionLocal()

    try:
        job: VideoJob = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job:
            raise Exception(f"VideoJob {job_id} not found")

        video: Video = db.query(Video).filter(Video.id == job.video_id).first()
        if not video:
            raise Exception(f"Video {job.video_id} not found for job {job.id}")

        provider = job.provider.upper()
        provider_mod = PROVIDERS.get(provider)
        if not provider_mod:
            raise Exception(f"Provider '{provider}' not supported")

        if not job.task_id:
            raise Exception(f"Job {job.id} has no task_id stored")

        logger.info(f"🔍 Polling provider {provider} for task_id={job.task_id}")

        # Provider returns:
        # { "status": "Processing|Success|Fail", "file_id": "...", "meta": {...} }
        poll_result = provider_mod.poll(job)

        # Save raw provider output
        if poll_result.get("meta"):
            job.meta = to_json(poll_result["meta"])

        # -----------------------------
        # PROCESSING
        # -----------------------------
        if poll_result["status"] == "processing":
            logger.info(f"⏳ Job {job.id} still processing...")
            job.attempts += 1
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "processing"}

        # -----------------------------
        # FAILED
        # -----------------------------
        if poll_result["status"] == "failed":
            logger.error(f"❌ Provider marked job {job.id} as FAILED")
            job.status = JobStatus.failed
            job.error_log = "Provider returned failure"
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "failed"}

        # -----------------------------
        # SUCCESS → retrieve file
        # -----------------------------
        file_id = poll_result.get("file_id")
        if not file_id:
            raise Exception(f"Success status but no file_id for job {job.id}")

        job.file_id = file_id
        db.commit()

        logger.info(f"📦 File ready for job {job.id}: file_id={file_id}")

        # retrieve file info
        retrieve_result = provider_mod.retrieve(file_id)
        download_url = retrieve_result.get("download_url")
        filename = retrieve_result.get("filename", f"{provider}_{job.task_id}.mp4")

        # final save path
        final_path = f"assets/videos/{provider.lower()}_{job.task_id}.mp4"

        # download file
        provider_mod.download(download_url, final_path)

        # update video
        video.file_url = final_path
        video.status = "uploaded"
        video.updated_at = datetime.now(timezone.utc)

        # update job
        job.local_path = final_path
        job.video_url = download_url
        job.status = JobStatus.success
        job.completed_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)

        db.commit()

        logger.info(f"🎉 Job {job.id} completed successfully → {final_path}")

        return {
            "status": "success",
            "file_path": final_path,
            "meta": retrieve_result.get("meta", {})
        }

    except Exception as e:
        logger.error(f"❌ Error processing running job {job_id}: {e}")
        logger.debug(traceback.format_exc())

        job.status = JobStatus.failed
        job.error_log = f"{type(e).__name__}: {str(e)}"
        job.updated_at = datetime.now(timezone.utc)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        return {"status": "failed", "error": str(e)}

    finally:
        db.close()
