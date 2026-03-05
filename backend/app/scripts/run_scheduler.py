import os
import time
import json
import logging
from datetime import datetime, timezone, timedelta

from app.db.database import SessionLocal
from app.models.video_job import VideoJob, JobStatus
from app.models.video import Video
from app.models.script import Script
from app.models.video_merge_job import VideoMergeJob, MergeStatus

from app.services.ai_video_service import (
    submit_job_to_provider,
    process_running_job,
)

from app.services.voice_generation_service import run_tts_video_job
from app.services.provider_router import choose_provider
from app.services.performance_service import can_dispatch_job
from app.services.engines.image_motion.image_motion_engine import (
    generate_image_motion_scene,
)

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

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/scheduler.log", encoding="utf-8")
    fh.setFormatter(formatter)

    scheduler_logger.addHandler(ch)
    scheduler_logger.addHandler(fh)

# =============================================================
# CONFIG
# =============================================================
POLL_INTERVAL = int(os.getenv("VIDEO_JOB_INTERVAL", 60))
VIDEO_COST_MODE = os.getenv("VIDEO_COST_MODE", "balanced").lower()
MAX_POLL_ATTEMPTS = int(os.getenv("MAX_POLL_ATTEMPTS", 5))
JOB_STALE_MINUTES = int(os.getenv("JOB_STALE_MINUTES", 15))


# =============================================================
# ♻️ STALE JOB RECOVERY
# =============================================================
def reset_stale_jobs(db):
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=JOB_STALE_MINUTES)

    stale_jobs = (
        db.query(VideoJob)
        .filter(
            VideoJob.status == JobStatus.running,
            VideoJob.updated_at < stale_time,
        )
        .with_for_update(skip_locked=True)
        .all()
    )

    for job in stale_jobs:
        scheduler_logger.warning(f"♻️ Resetting stale job {job.id}")
        job.status = JobStatus.queued
        job.attempts += 1
        job.updated_at = datetime.now(timezone.utc)

    if stale_jobs:
        db.flush()


# =============================================================
# 🔑 MERGE JOB CREATION
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
    db.flush()  # IMPORTANT: do not commit inside transaction


# =============================================================
# 🔊 TTS JOB HANDLER
# =============================================================
def process_tts_job(job: VideoJob, db):
    scheduler_logger.info(
        f"🔊 Executing TTS job {job.id} (script_id={job.script_id})"
    )

    try:
        job.status = JobStatus.running
        job.started_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)
        db.flush()

        run_tts_video_job(db=db, video_job_id=job.id)

        scheduler_logger.info(f"🎤 TTS job {job.id} completed successfully")

    except Exception as e:
        scheduler_logger.error(
            f"❌ TTS job {job.id} FAILED: {e}", exc_info=True
        )

        job.status = JobStatus.failed
        job.error_log = str(e)
        job.completed_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)
        db.flush()


# =============================================================
# 🔵 PROCESS QUEUED JOBS
# =============================================================
def process_queued_jobs():
    db = SessionLocal()
    try:
        with db.begin():

            reset_stale_jobs(db)

            queued_jobs = (
                db.query(VideoJob)
                .filter(VideoJob.status == JobStatus.queued)
                .order_by(VideoJob.created_at.asc())
                .with_for_update(skip_locked=True)
                .limit(5)
                .all()
            )

            if not queued_jobs:
                scheduler_logger.info("⏳ No queued jobs.")
                return

            for job in queued_jobs:

                # Skip marker jobs
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
                    process_tts_job(job, db)
                    continue

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
                # 🔄 Retry Routing
                # -------------------------------------------------
                if job.scene_index is not None and job.attempts >= 1:
                    script = (
                        db.query(Script)
                        .filter(Script.id == job.script_id)
                        .first()
                    )

                    if script and script.scene_timings:
                        decision = choose_provider(
                            scene_index=job.scene_index,
                            total_scenes=len(script.scene_timings),
                            attempts=job.attempts,
                            category_name="",
                            cost_mode=VIDEO_COST_MODE,
                        )

                        job.provider = decision["provider"]
                        job.provider_tier = decision["provider_tier"]
                        job.mode = decision["mode"]

                        scheduler_logger.info(
                            f"🔁 Retry routing for VideoJob {job.id} → "
                            f"provider={job.provider}, tier={job.provider_tier}"
                        )

                # -------------------------------------------------
                # 🎞️ HYBRID IMAGE MOTION
                # -------------------------------------------------
                meta = {}
                if job.meta:
                    try:
                        meta = json.loads(job.meta)
                    except Exception:
                        meta = {}

                if meta.get("image_motion", False):

                    scheduler_logger.info(
                        f"🎞️ Image Motion execution for VideoJob {job.id}"
                    )

                    try:
                        job.status = JobStatus.running
                        job.started_at = datetime.now(timezone.utc)
                        job.updated_at = datetime.now(timezone.utc)
                        db.flush()

                        video_path = generate_image_motion_scene(
                            prompt=meta.get("scene_prompt", ""),
                            duration=meta.get("duration_sec", 6),
                            script_id=job.script_id,
                            scene_index=job.scene_index,
                            scene_type=meta.get("scene_type", "normal"),
                        )

                        if not video_path or not os.path.exists(video_path):
                            raise RuntimeError("Image motion generation failed")

                        # ✅ Persist output path (CRITICAL FOR MERGE WORKER)
                        job.local_path = video_path

                        meta["file_path"] = video_path
                        job.meta = json.dumps(meta)

                        job.status = JobStatus.success
                        job.completed_at = datetime.now(timezone.utc)
                        job.updated_at = datetime.now(timezone.utc)

                        scheduler_logger.info(
                            f"✅ Image Motion SUCCESS | VideoJob {job.id} → {video_path}"
                        )

                        db.flush()

                        maybe_create_merge_job(
                            db=db,
                            video_id=job.video_id,
                            script_id=job.script_id,
                        )

                        continue

                    except Exception as e:
                        scheduler_logger.error(
                            f"❌ Image Motion FAILED for VideoJob {job.id}: {e}",
                            exc_info=True,
                        )

                        job.status = JobStatus.failed
                        job.error_log = str(e)
                        job.completed_at = datetime.now(timezone.utc)
                        job.updated_at = datetime.now(timezone.utc)
                        db.flush()
                        continue

                # -------------------------------------------------
                # 🚀 NORMAL PROVIDER FLOW
                # -------------------------------------------------
                if not job.provider:
                    raise RuntimeError(
                        f"Provider missing for VideoJob {job.id}"
                    )

                if not can_dispatch_job(db, job.provider):
                    scheduler_logger.info(
                        f"⏳ Performance throttle → skipping job {job.id} "
                        f"(provider={job.provider})"
                    )
                    continue

                scheduler_logger.info(
                    f"🚀 Submitting VideoJob {job.id} to provider={job.provider}"
                )

                submit_job_to_provider(job.id, db=db)
                db.refresh(job)

                if job.status == JobStatus.queued:
                    job.status = JobStatus.running
                    job.started_at = datetime.now(timezone.utc)
                    job.updated_at = datetime.now(timezone.utc)
                    db.flush()

    finally:
        db.close()


# =============================================================
# 🔵 PROCESS RUNNING JOBS
# =============================================================
def process_running_jobs():
    db = SessionLocal()
    try:
        with db.begin():

            running_jobs = (
                db.query(VideoJob)
                .filter(
                    VideoJob.status == JobStatus.running,
                    VideoJob.is_tts.is_(False),
                )
                .order_by(VideoJob.updated_at.asc())
                .with_for_update(skip_locked=True)
                .limit(10)
                .all()
            )

            if not running_jobs:
                scheduler_logger.info("⏳ No running jobs to poll.")
                return

            for job in running_jobs:
                try:
                    result = process_running_job(job.id, db=db)

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
                        error = result.get("error", "")

                        # 🟡 POLLING FAILURE → RETRY
                        if (
                            job.task_id
                            and is_polling_error(error)
                            and job.attempts < MAX_POLL_ATTEMPTS
                        ):
                            job.attempts += 1
                            job.updated_at = datetime.now(timezone.utc)
                            scheduler_logger.warning(
                                f"🔁 Polling retry {job.attempts}/{MAX_POLL_ATTEMPTS} "
                                f"for VideoJob {job.id}"
                            )
                            continue

                        # 🔴 HARD FAILURE (polling exhausted or non-retryable)
                        job.status = JobStatus.failed
                        job.error_log = error
                        job.completed_at = datetime.now(timezone.utc)

                        scheduler_logger.error(
                            f"❌ VideoJob {job.id} failed permanently: {error}"
                        )

                    job.updated_at = datetime.now(timezone.utc)
                    db.commit()

                except Exception as e:
                    # 🟡 Scheduler / infra error → polling retry
                    if (
                        job.task_id
                        and job.attempts < MAX_POLL_ATTEMPTS
                    ):
                        job.attempts += 1
                        job.status = JobStatus.running
                        job.error_log = str(e)
                        job.updated_at = datetime.now(timezone.utc)

                        scheduler_logger.warning(
                            f"🔁 Polling retry {job.attempts}/{MAX_POLL_ATTEMPTS} "
                            f"for VideoJob {job.id} due to exception"
                        )

                        db.commit()
                        continue

                    # 🔴 HARD FAILURE
                    job.status = JobStatus.failed
                    job.error_log = str(e)
                    job.completed_at = datetime.now(timezone.utc)
                    job.updated_at = datetime.now(timezone.utc)

                    scheduler_logger.error(
                        f"❌ VideoJob {job.id} permanently failed: {e}",
                        exc_info=True,
                    )

                    db.commit()

    finally:
        db.close()

def is_polling_error(error: str) -> bool:
    if not error:
        return False

    error = error.lower()
    return any(
        k in error
        for k in [
            "poll",
            "timeout",
            "network",
            "500",
            "temporary",
            "oss",
            "fetch",
        ]
    )

# =============================================================
# MAIN LOOP
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
