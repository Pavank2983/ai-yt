import os
import json
import logging
import subprocess
import time
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.models import Script, Video, Voice
from app.models.video_job import VideoJob, JobStatus

from app.utils import asset_paths

from app.services.video_edit.music_engine import mix_background_music
from app.services.video_edit.auto_music_policy import choose_music
from app.services.video_edit.subtitle_engine import generate_subtitles, burn_subtitles

from app.services.video_edit.caption_styles import srt_to_ass
from app.services.video_edit.auto_caption_policy import choose_caption_style, random_style
from app.services.video_edit.edit_cache import (
    compute_cache_key,
    check_cache,
    store_cache,
)

logger = logging.getLogger("video_editor")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/video_editor.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


# ============================================================
# CONFIG
# ============================================================

ENABLE_AUTO_BACKGROUND_MUSIC = (
    os.getenv("ENABLE_AUTO_BACKGROUND_MUSIC", "true").lower() == "true"
)

ENABLE_AUTO_SUBTITLES = (
    os.getenv("ENABLE_AUTO_SUBTITLES", "true").lower() == "true"
)

CAPTION_STYLE = os.getenv("CAPTION_STYLE", "auto").lower()

# ------------------------------------------------------------
# Editing Functions
# ------------------------------------------------------------
def normalize_audio(input_path: str, output_path: str):

    logger.info("🔊 Running ffmpeg loudnorm")

    subprocess.check_call([
        "ffmpeg",
        "-y",
        "-i", input_path,

        # SAFETY: allow videos without audio
        "-filter:a", "loudnorm",
        "-c:v", "copy",
        "-map", "0:v",
        "-map", "0:a?",

        output_path
    ])

def create_thumbnail_job(db, video, video_id, video_path):

    try:

        existing_thumb = (
            db.query(VideoJob)
            .filter(
                VideoJob.video_id == video_id,
                VideoJob.provider == "THUMBNAIL"
            )
            .first()
        )

        if existing_thumb:
            logger.info(
                "🖼 Thumbnail job already exists | video_id=%s",
                video_id
            )
            return

        logger.info(
            "🖼 Creating THUMBNAIL job | video_id=%s",
            video_id
        )

        thumb_job = VideoJob(
            script_id=video.script_id,
            video_id=video_id,
            provider="THUMBNAIL",
            provider_tier="LOCAL",
            mode="thumbnail",
            status=JobStatus.queued,
            meta=json.dumps({
                "input_video": video_path
            }),
            created_at=datetime.now(timezone.utc)
        )

        db.add(thumb_job)
        db.commit()

    except Exception as e:

        logger.warning(
            "⚠ Thumbnail job creation failed | %s",
            str(e)
        )

# ------------------------------------------------------------
# Main Worker
# ------------------------------------------------------------
def run_video_edit_job(job_id: int, db):
    job = db.get(VideoJob, job_id)
    
    if not job:
        raise RuntimeError(f"VideoJob not found: {job_id}")

    job_id = job.id
    
    # ------------------------------------------------
    # IDEMPOTENCY CHECK (Prevent duplicate edits)
    # ------------------------------------------------
    if job.local_path and os.path.exists(job.local_path):

        logger.info(
            "⚡ EDITOR job already completed earlier | job_id=%s | output=%s",
            job_id,
            job.local_path
        )

        video = db.query(Video).filter(Video.id == job.video_id).first()

        if video and video.file_url != job.local_path:
            video.file_url = job.local_path.replace("\\", "/")

            # Ensure thumbnail job exists
            create_thumbnail_job(db, video, video.id, job.local_path)

        job.status = JobStatus.success
        job.completed_at = job.completed_at or datetime.now(timezone.utc)

        db.commit()

        return

    try:
        logger.info(
            "🎬 EDITOR job started | job_id=%s",
            job_id
        )

        meta = json.loads(job.meta or "{}")

        input_video = meta.get("input_video")

        if not input_video:
            raise RuntimeError("input_video missing in job.meta")

        input_video = os.path.abspath(input_video)

        logger.info("🎞 Input video | %s", input_video)

        if not os.path.exists(input_video):
            raise RuntimeError(f"Input video missing: {input_video}")

        music_name = None
        voice_path = None
        cache_key = None

        # ------------------------------------------------
        # CACHE CHECK (NEW)
        # ------------------------------------------------
        try:            
            cache_key = compute_cache_key(
                input_video,
                CAPTION_STYLE,
                music_name,
                voice_path
            )

            cached_video = check_cache(cache_key)

            if cached_video and os.path.exists(cached_video):

                logger.info(
                    "⚡ Cache hit → skipping video edit pipeline | cache=%s",
                    cached_video
                )

                video = db.query(Video).filter(Video.id == job.video_id).first()

                # Normalize path before storing in DB
                normalized_path = cached_video.replace("\\", "/")

                if video:
                    video.file_url = normalized_path

                job.status = JobStatus.success
                job.local_path = normalized_path
                job.completed_at = datetime.now(timezone.utc)

                db.commit()

                logger.info(
                    "✅ EDITOR job complete (CACHE) | video_id=%s | output=%s",
                    job.video_id,
                    cached_video
                )
                
                create_thumbnail_job(db, video, video.id, cached_video)

                return

        except Exception as e:
            logger.warning(
                "⚠ Cache check failed → continuing normal edit pipeline | %s",
                str(e)
            )

        # ------------------------------------------------
        # 1️⃣ Normalize Audio
        # ------------------------------------------------
        if "_norm.mp4" in input_video:
            edited_video = input_video
        else:
            normalized = input_video.replace(".mp4", "_norm.mp4")

            logger.info("🔊 Normalizing audio → %s", normalized)

            normalize_audio(input_video, normalized)

            if not os.path.exists(normalized):
                raise RuntimeError("Audio normalization failed")

            edited_video = os.path.abspath(normalized)

        logger.info("🎞 Video after normalization | %s", edited_video)

        # ------------------------------------------------
        # 2️⃣ Load Video + Script
        # ------------------------------------------------
        video = db.query(Video).filter(Video.id == job.video_id).first()

        if not video:
            raise RuntimeError("Video record missing")

        video_id = video.id

        script = db.query(Script).filter(
            Script.id == video.script_id
        ).first()

        category_name = ""

        if script and getattr(script, "category", None):
            category_name = script.category.name

        logger.info(
            "🎬 Category detected | category=%s",
            category_name
        )

        # ------------------------------------------------
        # 3️⃣ Auto Background Music (ENV Controlled)
        # ------------------------------------------------
        if ENABLE_AUTO_BACKGROUND_MUSIC:

            try:

                music_name = choose_music(category_name)

                logger.info(
                    "🎵 Auto music selection | category=%s → music=%s",
                    category_name,
                    music_name
                )

                music_output = mix_background_music(
                    edited_video,
                    music_name
                )

                if music_output and os.path.exists(music_output):
                    edited_video = os.path.abspath(music_output)

                logger.info("🎞 Video after music | %s", edited_video)

            except Exception as e:

                logger.warning(
                    "⚠ Background music failed → using normalized video | %s",
                    str(e)
                )

        else:

            logger.info("🎵 Background music disabled via ENV")

        # ------------------------------------------------
        # 4️⃣ Auto Subtitles (ENV Controlled)
        # ------------------------------------------------
        if ENABLE_AUTO_SUBTITLES:

            voice = (
                db.query(Voice)
                .filter(
                    Voice.script_id == video.script_id,
                    Voice.is_primary.is_(True)
                )
                .first()
            )

            voice_path = voice.file_path if voice else None

            if voice_path and os.path.exists(voice_path):

                try:

                    logger.info("📝 Generating subtitles from voice | %s", voice_path)

                    subtitle_dir = os.path.join(
                        asset_paths.videos_root(video.script_id),
                        "subtitles"
                    )

                    os.makedirs(subtitle_dir, exist_ok=True)

                    subtitle_file = generate_subtitles(
                        voice_path,
                        subtitle_dir
                    )

                    if not subtitle_file or not os.path.exists(subtitle_file):
                        raise RuntimeError("Subtitle generation returned invalid file")

                    logger.info("📝 SRT generated | %s", subtitle_file)

                    if CAPTION_STYLE == "auto":
                        style = choose_caption_style(category_name)

                    elif CAPTION_STYLE == "random":
                        style = random_style()

                    else:
                        style = CAPTION_STYLE

                    logger.info(
                        "📝 Caption style selected → %s",
                        style
                    )

                    ass_file = srt_to_ass(
                        subtitle_file,
                        style
                    )

                    if not ass_file or not os.path.exists(ass_file):
                        raise RuntimeError("ASS subtitle generation failed")

                    logger.info("📝 ASS subtitle generated | %s", ass_file)

                    logger.info("🔥 Burning subtitles into video")

                    caption_output = burn_subtitles(
                        edited_video,
                        ass_file
                    )

                    if caption_output and os.path.exists(caption_output):
                        edited_video = asset_paths.to_relative(caption_output)
                        edited_video = edited_video.replace("\\", "/")

                    logger.info("🎞 Video after subtitles | %s", edited_video)

                except Exception as e:

                    logger.warning(
                        "⚠ Subtitle generation failed → skipping | %s",
                        str(e)
                    )

            else:

                logger.info(
                    "📝 No voice track available → skipping subtitles"
                )

        else:

            logger.info("📝 Auto subtitles disabled via ENV")

        # ------------------------------------------------
        # CACHE STORE (NEW)
        # ------------------------------------------------
        try:
            store_cache(cache_key, edited_video)
            logger.info(
                "💾 Stored edited video in cache | key=%s",
                cache_key
            )
        except Exception as e:
            logger.warning(
                "⚠ Cache store failed | %s",
                str(e)
            )

        # ------------------------------------------------
        # 5️⃣ Update Video Record
        # ------------------------------------------------
        logger.info(
            "📝 Updating video record | video_id=%s",
            video_id
        )

        # Normalize path before storing in DB
        normalized_path = edited_video.replace("\\", "/")

        video.file_url = normalized_path

        # ------------------------------------------------
        # 6️⃣ Update Job
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
                logger.warning("DB commit retry %s | %s", attempt + 1, str(e))
                db.rollback()
                time.sleep(2)

        if not success:
            raise RuntimeError("DB commit failed after retries")

        logger.info(
            "✅ EDITOR job complete | video_id=%s | output=%s",
            video_id,
            edited_video
        )
        
        # ------------------------------------------------
        # 🖼 CREATE THUMBNAIL JOB
        # ------------------------------------------------
        create_thumbnail_job(db, video, video_id, edited_video)

    except Exception as e:

        logger.error(
            "❌ EDITOR job failed | job_id=%s → %s",
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