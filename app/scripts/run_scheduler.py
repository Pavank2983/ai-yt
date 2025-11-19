import os
import time
import logging
import traceback
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.models.video_job import VideoJob, JobStatus
from app.services.ai_video_service import (
    submit_job_to_provider,
    process_running_job
)

# Logger
scheduler_logger = logging.getLogger("scheduler_logger")
scheduler_logger.setLevel(logging.INFO)

if not scheduler_logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    console_handler.setFormatter(formatter)
    scheduler_logger.addHandler(console_handler)

# Run interval
POLL_INTERVAL = int(os.getenv("VIDEO_JOB_INTERVAL", 60))


# -------------------------------------------------------------
# 🔵 PROCESS QUEUED JOBS → SUBMIT TO PROVIDER
# -------------------------------------------------------------
def process_queued_jobs():
    db = SessionLocal()

    try:
        queued_jobs = (
            db.query(VideoJob)
            .filter(VideoJob.status == JobStatus.queued)
            .order_by(VideoJob.created_at.asc())
            .limit(5)
            .all()
        )

        if not queued_jobs:
            scheduler_logger.info("⏳ No queued jobs.")
            return

        scheduler_logger.info(f"⚙️ Found {len(queued_jobs)} queued job(s).")

        for job in queued_jobs:
            try:
                scheduler_logger.info(
                    f"🚀 Submitting job {job.id} (video_id={job.video_id}) to provider {job.provider}"
                )

                # Mark job running (submission phase)
                job.status = JobStatus.running
                job.started_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                db.commit()

                # Submit to provider (returns immediate or queued metadata)
                submit_result = submit_job_to_provider(job.id)

                # If provider returned instant video (file_path exists)
                if submit_result.get("file_path"):
                    scheduler_logger.info(f"✅ Job {job.id} completed instantly.")
                    job.status = JobStatus.success
                    job.completed_at = datetime.now(timezone.utc)

                else:
                    scheduler_logger.info(
                        f"⏳ Job {job.id} queued on provider. Waiting for async completion."
                    )

                # Save job meta
                if "meta" in submit_result:
                    job.meta = submit_result["meta"]

                db.commit()

            except Exception as e:
                scheduler_logger.error(f"❌ Error submitting job {job.id}: {e}")
                tb = traceback.format_exc()

                job.status = JobStatus.failed
                job.error_log = f"{type(e).__name__}: {e}\n{tb}"
                job.updated_at = datetime.now(timezone.utc)
                db.commit()

    finally:
        db.close()


# -------------------------------------------------------------
# 🔵 PROCESS RUNNING JOBS → POLL PROVIDER (MINIMAX)
# -------------------------------------------------------------
def process_running_jobs():
    db = SessionLocal()

    try:
        running_jobs = (
            db.query(VideoJob)
            .filter(VideoJob.status == JobStatus.running)
            .order_by(VideoJob.updated_at.asc())
            .limit(10)
            .all()
        )

        if not running_jobs:
            scheduler_logger.info("⏳ No running jobs to poll.")
            return

        scheduler_logger.info(f"🔄 Polling {len(running_jobs)} running job(s)...")

        for job in running_jobs:
            try:
                scheduler_logger.info(
                    f"🔍 Polling job {job.id} (provider={job.provider}, task_id={job.task_id})"
                )

                result = process_running_job(job.id)

                # Merge returned metadata
                if "meta" in result:
                    job.meta = result["meta"]

                # If job finished
                if result.get("status") == "success":
                    scheduler_logger.info(f"🎉 Job {job.id} completed successfully.")
                    job.status = JobStatus.success
                    job.completed_at = datetime.now(timezone.utc)

                elif result.get("status") == "failed":
                    scheduler_logger.error(f"❌ Job {job.id} FAILED.")
                    job.status = JobStatus.failed
                    job.error_log = str(result.get("error", "provider reported failure"))
                    job.completed_at = datetime.now(timezone.utc)

                job.updated_at = datetime.now(timezone.utc)
                db.commit()

            except Exception as e:
                tb = traceback.format_exc()
                scheduler_logger.error(f"❌ Error polling job {job.id}: {e}")

                job.status = JobStatus.failed
                job.error_log = f"{type(e).__name__}: {e}\n{tb}"
                job.updated_at = datetime.now(timezone.utc)
                job.completed_at = datetime.now(timezone.utc)

                db.commit()

    finally:
        db.close()


# -------------------------------------------------------------
# 🔵 MAIN LOOP
# -------------------------------------------------------------
def run_scheduler():
    scheduler_logger.info("🕒 Video Job Scheduler Started")

    ONE_SHOT = os.getenv("VIDEO_JOB_ONE_SHOT", "false").lower() == "true"

    while True:
        try:
            # 1️⃣ Submit queued jobs
            process_queued_jobs()

            # 2️⃣ Poll running jobs (MiniMax)
            process_running_jobs()

        except Exception as loop_err:
            scheduler_logger.error(f"⚠️ Scheduler Loop Error: {loop_err}")
            scheduler_logger.debug(traceback.format_exc())

        if ONE_SHOT:
            scheduler_logger.info("🛑 ONE_SHOT enabled → stopping scheduler.")
            break

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_scheduler()
