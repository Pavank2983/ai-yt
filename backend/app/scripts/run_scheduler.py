import os
import time
import json
import logging
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.models.video_job import VideoJob, JobStatus
from app.models.video import Video
from app.models.script import Script
from app.models.video_merge_job import VideoMergeJob, MergeStatus

from app.services.ai_video_service import (
    submit_job_to_provider,
    process_running_job,
)

from app.services.voice_generation_service import generate_voice_for_script
from app.services.orchestrator.scene_job_orchestrator import SceneJobOrchestrator

# =============================================================
# LOGGER
# =============================================================
scheduler_logger = logging.getLogger("scheduler")
scheduler_logger.setLevel(logging.INFO)

if not scheduler_logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    # Console output
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    # File output
    fh = logging.FileHandler("logs/scheduler.log", encoding="utf-8")
    fh.setFormatter(formatter)

    scheduler_logger.addHandler(ch)
    scheduler_logger.addHandler(fh)

# =============================================================
# CONFIG
# =============================================================
POLL_INTERVAL = int(os.getenv("VIDEO_JOB_INTERVAL", 60))
AI_VIDEO_PROVIDER = os.getenv("AI_VIDEO_PROVIDER", "MINIMAX").upper()
USE_TTS_PROVIDER = os.getenv("USE_TTS_PROVIDER", "elevenlabs").lower()


# =============================================================
# 🔑 MERGE JOB CREATION HELPER
# =============================================================
def maybe_create_merge_job(db, video_id: int, script_id: int):
    """
    Create a VideoMergeJob ONLY if:
    - all scene jobs are success
    - no merge job already exists
    """

    # Check all scene jobs
    scene_jobs = (
        db.query(VideoJob)
        .filter(
            VideoJob.video_id == video_id,
            VideoJob.scene_index.isnot(None),
        )
        .all()
    )

    if not scene_jobs:
        return

    if not all(j.status == JobStatus.success for j in scene_jobs):
        return

    # Check existing merge job
    existing = (
        db.query(VideoMergeJob)
        .filter(VideoMergeJob.video_id == video_id)
        .first()
    )

    if existing:
        return

    scheduler_logger.info(
        f"🧩 All scenes completed → creating merge job for video_id={video_id}"
    )

    merge_job = VideoMergeJob(
        video_id=video_id,
        script_id=script_id,
        status=MergeStatus.pending,
        created_at=datetime.now(timezone.utc),
    )

    db.add(merge_job)
    db.commit()


# =============================================================
# 🔊 TTS JOB HANDLER
# =============================================================
def process_tts_job(job: VideoJob, db):
    scheduler_logger.info(
        f"🔊 Running TTS job {job.id} (script_id={job.script_id})"
    )

    try:
        meta = json.loads(job.meta or "{}")

        script = db.query(Script).filter(Script.id == job.script_id).first()
        if not script:
            raise RuntimeError("Script not found for TTS job")

        result = generate_voice_for_script(
            db=db,
            script=script,
            provider=USE_TTS_PROVIDER,
            voice_name=meta.get("voice"),
        )

        job.status = JobStatus.success
        job.completed_at = datetime.now(timezone.utc)
        job.meta = json.dumps({
            **meta,
            "voice_path": result["file_path"],
            "duration": result.get("duration"),
        })
        db.commit()

        scheduler_logger.info(f"🎤 TTS job {job.id} completed successfully")

        scene_orchestrator = SceneJobOrchestrator(
            db=db,
            script_id=script.id,
            scenes=script.scene_timings,
            voice_length_seconds=script.audio_duration_seconds,
            provider=AI_VIDEO_PROVIDER,
            quality="STANDARD",
        )

        scene_orchestrator.run()

    except Exception as e:
        scheduler_logger.error(
            f"❌ TTS job {job.id} FAILED: {e}", exc_info=True
        )

        job.status = JobStatus.failed
        job.error_log = str(e)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        if job.video_id:
            video = db.query(Video).filter(Video.id == job.video_id).first()
            if video:
                video.status = "failed"
                video.is_active = 0
                db.commit()


# =============================================================
# 🔵 PROCESS QUEUED JOBS
# =============================================================
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

        for job in queued_jobs:
            try:
                # -------------------------------------------------
                # 🚫 SKIP orchestration / marker jobs
                # -------------------------------------------------
                # These are VideoJob rows created only to track orchestration
                # They must NEVER be executed by the scheduler
                if (
                    job.scene_index is None
                    and not job.is_tts
                    and job.provider is None
                ):
                    scheduler_logger.info(
                        f"⏭️ Skipping orchestration marker job {job.id}"
                    )
                    continue

                # -------------------------------------------------
                # 🔊 TTS JOBS (ABSOLUTE PRIORITY)
                # -------------------------------------------------
                if job.is_tts:
                    scheduler_logger.info(
                        f"🔊 Executing TTS job {job.id} (script_id={job.script_id})"
                    )

                    job.status = JobStatus.running
                    job.started_at = datetime.now(timezone.utc)
                    job.updated_at = datetime.now(timezone.utc)
                    db.commit()

                    process_tts_job(job, db)
                    continue  # 🚨 NEVER fall through

                # -------------------------------------------------
                # ⏸️ SCENE JOBS MUST WAIT FOR TTS
                # -------------------------------------------------
                if job.scene_index is not None:
                    tts_jobs = (
                        db.query(VideoJob)
                        .filter(
                            VideoJob.video_id == job.video_id,
                            VideoJob.is_tts.is_(True),
                        )
                        .all()
                    )

                    if tts_jobs and not all(
                        t.status == JobStatus.success for t in tts_jobs
                    ):
                        scheduler_logger.info(
                            f"⏸️ Scene job {job.id} waiting for TTS completion"
                        )
                        continue

                # -------------------------------------------------
                # 🚀 AI VIDEO PROVIDER JOBS (SCENE JOBS)
                # -------------------------------------------------
                if not job.provider:
                    raise RuntimeError(
                        f"Provider missing for VideoJob {job.id}"
                    )

                scheduler_logger.info(
                    f"🚀 Submitting VideoJob {job.id} to provider={job.provider}"
                )

                job.status = JobStatus.running
                job.started_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                db.commit()

                submit_result = submit_job_to_provider(job.id)

                if submit_result.get("file_path"):
                    job.status = JobStatus.success
                    job.completed_at = datetime.now(timezone.utc)

                if "meta" in submit_result:
                    job.meta = submit_result["meta"]

                db.commit()

            except Exception as e:
                scheduler_logger.error(
                    f"❌ Error processing queued job {job.id}: {e}",
                    exc_info=True,
                )
                job.status = JobStatus.failed
                job.error_log = str(e)
                job.updated_at = datetime.now(timezone.utc)
                db.commit()

    finally:
        db.close()

# =============================================================
# 🔵 PROCESS RUNNING PROVIDER JOBS
# =============================================================
def process_running_jobs():
    db = SessionLocal()
    try:
        running_jobs = (
            db.query(VideoJob)
            .filter(
                VideoJob.status == JobStatus.running,
                VideoJob.is_tts.is_(False),
            )
            .order_by(VideoJob.updated_at.asc())
            .limit(10)
            .all()
        )

        if not running_jobs:
            scheduler_logger.info("⏳ No running jobs to poll.")
            return

        for job in running_jobs:
            try:
                result = process_running_job(job.id)

                if "meta" in result:
                    job.meta = result["meta"]

                if result.get("status") == "success":
                    job.status = JobStatus.success
                    job.completed_at = datetime.now(timezone.utc)

                    # 🔑 CHECK FOR MERGE TRIGGER
                    if job.scene_index is not None:
                        maybe_create_merge_job(
                            db=db,
                            video_id=job.video_id,
                            script_id=job.script_id,
                        )

                elif result.get("status") == "failed":
                    job.status = JobStatus.failed
                    job.error_log = str(result.get("error"))
                    job.completed_at = datetime.now(timezone.utc)

                job.updated_at = datetime.now(timezone.utc)
                db.commit()

            except Exception as e:
                scheduler_logger.error(
                    f"❌ Error polling job {job.id}: {e}", exc_info=True
                )
                job.status = JobStatus.failed
                job.error_log = str(e)
                job.completed_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                db.commit()
    finally:
        db.close()


# =============================================================
# 🔵 MAIN LOOP
# =============================================================
def run_scheduler():
    scheduler_logger.info("🕒 Video Job Scheduler Started")

    ONE_SHOT = os.getenv("VIDEO_JOB_ONE_SHOT", "false").lower() == "true"

    while True:
        process_queued_jobs()
        process_running_jobs()

        if ONE_SHOT:
            scheduler_logger.info("🛑 ONE_SHOT enabled → stopping scheduler.")
            break

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_scheduler()
