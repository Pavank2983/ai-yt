import os
import json
import logging
import time
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.models.video import Video
from app.models.script import Script
from app.models.video_job import VideoJob, JobStatus

from app.services.thumbnail.thumbnail_engine import generate_thumbnail
from app.services.notifications.whatsapp_service import send_video_review_notification

logger = logging.getLogger("thumbnail_engine")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/thumbnail_engine.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


# ============================================================
# MAIN WORKER
# ============================================================
def run_thumbnail_job(job_id: int, db):

    job = db.get(VideoJob, job_id)

    if not job:
        raise RuntimeError(f"VideoJob not found: {job_id}")

    job_id = job.id

    try:

        logger.info(
            "🖼 THUMBNAIL job started | job_id=%s",
            job_id
        )

        meta = json.loads(job.meta or "{}")

        input_video = meta.get("input_video")

        if not input_video:
            raise RuntimeError("input_video missing in job.meta")

        input_video = os.path.abspath(input_video)

        if not os.path.exists(input_video):
            raise RuntimeError(f"Input video missing: {input_video}")

        # ------------------------------------------------
        # Load video record
        # ------------------------------------------------
        video = db.query(Video).filter(Video.id == job.video_id).first()

        if not video:
            raise RuntimeError("Video record missing")

        video_id = video.id

        # ------------------------------------------------
        # Load script title
        # ------------------------------------------------
        script = db.query(Script).filter(
            Script.id == video.script_id
        ).first()

        script_title = script.title if script else "AI Video"

        logger.info(
            "📝 Script title detected | %s",
            script_title
        )

        # ------------------------------------------------
        # Prepare thumbnail output directory
        # ------------------------------------------------
        output_dir = os.path.join(
            "assets",
            "output",
            f"script_{video.script_id}",
            "thumbnails"
        )

        os.makedirs(output_dir, exist_ok=True)

        # ------------------------------------------------
        # Generate thumbnail
        # ------------------------------------------------
        thumbnail_path = generate_thumbnail(
            video_path=input_video,
            script_title=script_title,
            output_dir=output_dir
        )

        if not thumbnail_path or not os.path.exists(thumbnail_path):
            raise RuntimeError("Thumbnail generation failed")

        logger.info(
            "🖼 Thumbnail generated | %s",
            thumbnail_path
        )

        # ------------------------------------------------
        # Update video record
        # ------------------------------------------------
        # Normalize path before storing in DB
        normalized_path = thumbnail_path.replace("\\", "/")

        video.thumbnail_url = normalized_path
        video.status = "ready_for_review"

        # ------------------------------------------------
        # Update job
        # ------------------------------------------------
        job.status = JobStatus.success
        job.local_path = normalized_path
        job.completed_at = datetime.now(timezone.utc)

        success = False

        for attempt in range(3):

            try:

                db.commit()
                success = True
                break

            except Exception as e:

                logger.warning(
                    "DB commit retry %s | %s",
                    attempt + 1,
                    str(e)
                )

                db.rollback()
                time.sleep(2)

        if not success:
            raise RuntimeError("DB commit failed after retries")

        logger.info(
            "✅ THUMBNAIL job complete | video_id=%s | output=%s",
            video_id,
            thumbnail_path
        )
        
        # ------------------------------------------------
        # 📲 Send WhatsApp review notification
        # ------------------------------------------------
        try:
            send_video_review_notification(db, video)
        except Exception as e:
            logger.error(
                "⚠ WhatsApp notification failed | video_id=%s | error=%s",
                video.id,
                str(e)
            )

    except Exception as e:

        logger.error(
            "❌ THUMBNAIL job failed | job_id=%s → %s",
            job_id,
            str(e),
            exc_info=True
        )

        db.rollback()

        job = db.get(VideoJob, job_id)

        if job:
            job.status = JobStatus.failed
            job.error_log = str(e)
            db.commit()