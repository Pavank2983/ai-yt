import os
import json
import logging
import traceback
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
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

from app.utils.publish_time import get_publish_time

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


def _claim_upload_status(db, video_id: int, platform_id: int):
    """Lock or create the single upload-status row for a video/platform pair."""

    from app.models.video_platform_status import (
        PlatformUploadStatus,
        VideoPlatformStatus,
    )

    status_row = (
        db.query(VideoPlatformStatus)
        .filter(
            VideoPlatformStatus.video_id == video_id,
            VideoPlatformStatus.platform_id == platform_id,
        )
        .with_for_update()
        .first()
    )
    if status_row is not None:
        return status_row

    status_row = VideoPlatformStatus(
        video_id=video_id,
        platform_id=platform_id,
        status=PlatformUploadStatus.pending,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(status_row)
    try:
        # The unique constraint closes the race where two transactions both
        # observe no existing row. The loser reloads the committed row.
        db.flush()
        return status_row
    except IntegrityError:
        db.rollback()
        return (
            db.query(VideoPlatformStatus)
            .filter(
                VideoPlatformStatus.video_id == video_id,
                VideoPlatformStatus.platform_id == platform_id,
            )
            .with_for_update()
            .one()
        )

def calculate_retry_delay(attempt: int) -> int:
    """
    Exponential backoff delay in seconds
    """
    base_delay = int(os.getenv("UPLOAD_RETRY_BASE_DELAY", 30))
    return base_delay * (2 ** max(0, attempt - 1))

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

        # =========================================================
        # 🆕 UPLOAD PROVIDER (MULTI-PLATFORM READY)
        # =========================================================
        if provider == "UPLOAD":

            logger.info(
                f"📤 Processing UPLOAD job | job_id={job.id} | video_id={video.id}"
            )

            approval_status = getattr(video.approval_status, "value", video.approval_status)
            if approval_status != "approved":
                raise Exception("Upload blocked: video has not been approved")

            # -----------------------------------------------------
            # Resolve platform from meta (Option A)
            # -----------------------------------------------------
            meta = from_json(job.meta)

            platform_name = (meta.get("platform") or "").lower().strip()

            if not platform_name:
                raise Exception("UPLOAD job missing platform in meta")

            # -----------------------------------------------------
            # Validate video file exists
            # -----------------------------------------------------
            file_path = video.file_url

            if not file_path:
                raise Exception("Video file_url missing for upload")

            file_path = file_path.replace("\\", "/")

            local_path = file_path
            if local_path.startswith("/"):
                local_path = local_path[1:]

            local_path = os.path.join(os.getcwd(), local_path)

            if not os.path.exists(local_path):
                raise Exception(f"Upload file not found: {local_path}")

            # -----------------------------------------------------
            # 🆕 UPDATE PLATFORM STATUS → uploading
            # -----------------------------------------------------
            from app.models.video_platform_status import VideoPlatformStatus, PlatformUploadStatus
            from app.models.platform import Platform

            platform = (
                db.query(Platform)
                .filter(Platform.name == platform_name)
                .first()
            )

            if not platform:
                raise Exception(f"Platform not found: {platform_name}")

            status_row = _claim_upload_status(db, video.id, platform.id)

            # -----------------------------------------------------
            # 🆕 UPSERT PLATFORM STATUS → uploading (CORRECT PLACE)
            # -----------------------------------------------------
            if status_row.status == PlatformUploadStatus.success and status_row.uploaded_url:
                job.status = JobStatus.success
                job.video_url = status_row.uploaded_url
                job.completed_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                if own_session:
                    db.commit()
                return {
                    "status": "success",
                    "uploaded_url": status_row.uploaded_url,
                    "reused": True,
                }

            status_row.status = PlatformUploadStatus.uploading
            status_row.error = None
            status_row.updated_at = datetime.now(timezone.utc)

            # -----------------------------------------------------
            # 🚀 REAL UPLOAD ROUTING
            # -----------------------------------------------------
            logger.info(
                f"🚀 Uploading video → platform={platform_name} | video_id={video.id}"
            )

            uploaded_url = None

            try:

                if platform_name == "youtube":

                    from app.services.platforms.youtube_service import upload_video, upload_thumbnail, upload_captions

                    uploaded = upload_video(
                        video=video,
                        file_path=local_path
                    )

                    youtube_id = uploaded["youtube_id"]
                    uploaded_url = uploaded["youtube_url"]

                    # -----------------------------------
                    # 🔥 Upload thumbnail
                    # -----------------------------------
                    thumbnail_path = video.thumbnail_url  # or your actual path

                    if thumbnail_path:
                        upload_thumbnail(youtube_id, thumbnail_path)

                    # -----------------------------------
                    # 📝 Captions
                    # -----------------------------------
                    srt_path = None

                    # Try to get from your pipeline (adjust path)
                    if hasattr(video, "voice_file_url") and video.voice_file_url:
                        srt_path = video.voice_file_url.replace(".mp3", ".srt")

                    if srt_path and os.path.exists(srt_path):
                        upload_captions(youtube_id, srt_path)

                elif platform_name == "instagram":
                    raise NotImplementedError("Instagram upload not implemented yet")

                else:
                    raise Exception(f"Unsupported platform: {platform_name}")

            except Exception as upload_error:

                logger.error(
                    f"❌ Upload failed | platform={platform_name} | video_id={video.id} | error={upload_error}",
                    exc_info=True
                )

                MAX_UPLOAD_RETRIES = int(os.getenv("UPLOAD_MAX_RETRIES", 3))

                job.attempts = (job.attempts or 0) + 1
                job.error_log = str(upload_error)
                job.updated_at = datetime.now(timezone.utc)

                # -----------------------------------------------------
                # 🔁 RETRY LOGIC WITH BACKOFF
                # -----------------------------------------------------
                if job.attempts < MAX_UPLOAD_RETRIES:

                    delay_seconds = calculate_retry_delay(job.attempts)

                    logger.warning(
                        f"🔁 Upload retry {job.attempts}/{MAX_UPLOAD_RETRIES} | "
                        f"delay={delay_seconds}s | video_id={video.id} | platform={platform_name}"
                    )

                    # ⏱ Delay next execution
                    job.status = JobStatus.queued
                    job.updated_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

                    if status_row:
                        status_row.status = PlatformUploadStatus.pending
                        status_row.error = str(upload_error)
                        status_row.updated_at = datetime.now(timezone.utc)

                    if own_session:
                        db.commit()

                    return {
                        "status": "retrying",
                        "attempt": job.attempts,
                        "next_retry_in_sec": delay_seconds
                    }

                # -----------------------------------------------------
                # 🔴 FINAL FAILURE
                # -----------------------------------------------------
                logger.error(
                    f"💀 Upload permanently failed after {MAX_UPLOAD_RETRIES} attempts | "
                    f"video_id={video.id} | platform={platform_name}"
                )

                job.status = JobStatus.failed
                job.completed_at = datetime.now(timezone.utc)

                if status_row:
                    status_row.status = PlatformUploadStatus.failed
                    status_row.error = str(upload_error)
                    status_row.updated_at = datetime.now(timezone.utc)

                if own_session:
                    db.commit()

                return {
                    "status": "failed",
                    "error": str(upload_error)
                }
            # -----------------------------------------------------
            # 🆕 MARK SUCCESS
            # -----------------------------------------------------
            if status_row:
                status_row.status = PlatformUploadStatus.success
                status_row.uploaded_url = uploaded_url
                status_row.error = None
                status_row.updated_at = datetime.now(timezone.utc)

            # -----------------------------------------------------
            # Mark job success
            # -----------------------------------------------------
            job.status = JobStatus.success
            job.local_path = file_path
            job.completed_at = datetime.now(timezone.utc)
            job.updated_at = datetime.now(timezone.utc)

            logger.info(
                f"✅ UPLOAD completed | video_id={video.id} | platform={platform_name}"
            )

            # -----------------------------------------------------
            # 🆕 SAFE CHECK (ENSURE CURRENT PLATFORM SUCCESS)
            # -----------------------------------------------------
            current_platform_done = (
                status_row and status_row.status == PlatformUploadStatus.success
            )

            all_status = (
                db.query(VideoPlatformStatus)
                .filter(VideoPlatformStatus.video_id == video.id)
                .all()
            )

            all_done = all_status and all(
                s.status == PlatformUploadStatus.success for s in all_status
            )

            if current_platform_done and all_done:
                # -----------------------------------------------------
                # 🧠 DO NOT mark as published yet
                # -----------------------------------------------------
                video.status = "uploaded"

                logger.info(
                    f"📦 Video uploaded (awaiting publish) | video_id={video.id}"
                )

                # -----------------------------------------------------
                # 🆕 CREATE PUBLISH JOB (CRITICAL)
                # -----------------------------------------------------

                now = datetime.now(timezone.utc)
                publish_time = get_publish_time(now)

                publish_job = VideoJob(
                    video_id=video.id,
                    script_id=video.script_id,
                    provider="PUBLISH",
                    status=JobStatus.queued,
                    meta=json.dumps({
                        "platform": platform_name,
                        "publish_at": publish_time.isoformat()
                    }),
                    created_at=datetime.now(timezone.utc)
                )

                existing_publish = (
                    db.query(VideoJob)
                    .filter(
                        VideoJob.video_id == video.id,
                        VideoJob.provider == "PUBLISH",
                        VideoJob.status.in_([JobStatus.queued, JobStatus.running])
                    )
                    .first()
                )

                if not existing_publish:
                    db.add(publish_job)

                logger.info(
                    f"📅 Scheduled publish job | video_id={video.id} | publish_at={publish_time}"
                )

            # -----------------------------------------------------
            # FINAL COMMIT (CRITICAL FIX)
            # -----------------------------------------------------
            db.commit()

            return {
                "status": "success",
                "file_path": file_path,
            }

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
            # Normalize path before storing in DB
            normalized_path = submit_result["file_path"].replace("\\", "/")
            job.local_path = normalized_path
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
                "file_path": normalized_path,
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
        final_path = final_path.replace("\\", "/")

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
