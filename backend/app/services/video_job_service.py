import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.video_job import VideoJob, JobStatus
from app.services.ai_video_service import (
    submit_job_to_provider,
    process_running_job
)

scheduler_logger = logging.getLogger("scheduler_logger")

# -------------------------------------------------------------
# SCAN QUEUED JOBS → SUBMIT TO PROVIDER
# -------------------------------------------------------------
def process_queued_jobs(limit: int = 5):
    """
    Submits ONLY executable scene jobs to AI providers.
    Skips:
      - Orchestrator marker jobs
      - TTS jobs
      - Jobs without provider
    """

    db: Session = SessionLocal()

    try:
        queued = (
            db.query(VideoJob)
            .filter(VideoJob.status == JobStatus.queued)
            .order_by(VideoJob.created_at.asc())
            .limit(limit)
            .all()
        )

        if not queued:
            scheduler_logger.info("🟢 No queued jobs found.")
            return

        scheduler_logger.info(f"⚙️ Evaluating {len(queued)} queued job(s)...")

        for job in queued:
            try:
                # -------------------------------------------------
                # 🚫 Skip orchestration marker jobs
                # -------------------------------------------------
                if (
                    not job.is_tts
                    and job.scene_index is None
                    and job.provider is None
                ):
                    scheduler_logger.info(
                        f"⏭️ Skipping orchestration marker job {job.id}"
                    )
                    continue

                # -------------------------------------------------
                # 🚫 Skip TTS jobs (handled elsewhere)
                # -------------------------------------------------
                if job.is_tts:
                    scheduler_logger.info(
                        f"⏭️ Skipping TTS job {job.id} (handled by TTS worker)"
                    )
                    continue

                # -------------------------------------------------
                # 🚫 Skip invalid jobs
                # -------------------------------------------------
                if job.scene_index is None or not job.provider:
                    scheduler_logger.warning(
                        f"⚠️ Skipping invalid VideoJob {job.id} "
                        f"(scene_index={job.scene_index}, provider={job.provider})"
                    )
                    continue

                # -------------------------------------------------
                # 🚀 Submit SCENE JOB to AI provider
                # -------------------------------------------------
                scheduler_logger.info(
                    f"🚀 Submitting Scene Job {job.id} | "
                    f"scene={job.scene_index} | provider={job.provider}"
                )

                job.status = JobStatus.running
                job.started_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                db.commit()

                result = submit_job_to_provider(job.id)

                scheduler_logger.info(
                    f"📨 Provider accepted Job {job.id} "
                    f"(task_id={result.get('task_id')})"
                )

            except Exception as e:
                scheduler_logger.error(
                    f"❌ Error submitting Job {job.id}: {e}",
                    exc_info=True
                )
                job.status = JobStatus.failed
                job.error_log = str(e)
                job.updated_at = datetime.now(timezone.utc)
                db.commit()

    finally:
        db.close()

# -------------------------------------------------------------
# SCAN RUNNING JOBS → POLL PROVIDER
# -------------------------------------------------------------
def process_running_jobs(limit: int = 5):
    """
    Poll jobs that have already been submitted.
    This is NOT the scheduler; only a helper for manual triggering.
    """

    db: Session = SessionLocal()

    try:
        running = (
            db.query(VideoJob)
            .filter(VideoJob.status == JobStatus.running)
            .order_by(VideoJob.updated_at.asc())
            .limit(limit)
            .all()
        )

        if not running:
            scheduler_logger.info("🟢 No running jobs found.")
            return

        scheduler_logger.info(f"🔄 Polling {len(running)} running job(s)...")

        for job in running:
            scheduler_logger.info(
                f"🔍 Polling Job {job.id} | provider={job.provider} | task_id={job.task_id} | file=Video_Job_Service.py"
            )

            try:
                result = process_running_job(job.id)

                if result["status"] == "success":
                    scheduler_logger.info(
                        f"🎉 Job {job.id} completed successfully"
                    )

                elif result["status"] == "processing":
                    scheduler_logger.info(
                        f"⏳ Job {job.id} still processing..."
                    )

                elif result["status"] == "failed":
                    scheduler_logger.error(
                        f"❌ Job {job.id} reported failure (scheduler will decide)"
                    )

            except Exception as e:
                # ⚠️ DO NOT mutate job status here
                scheduler_logger.error(
                    f"❌ Error polling Job {job.id}: {e}",
                    exc_info=True
                )

    finally:
        db.close()
