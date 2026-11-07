import os
import logging
import time
from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger("youtube_service")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/youtube_service.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

# 🆕 Configurable
YOUTUBE_CATEGORY_ID = os.getenv("YOUTUBE_CATEGORY_ID", "22")  # default: People & Blogs

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


# ---------------------------------------------------------
# AUTH
# ---------------------------------------------------------
def get_youtube_client():
    """
    Creates authenticated YouTube client using saved token file
    """

    token_path = "credentials/youtube_token.json"

    if not os.path.exists(token_path):
        raise RuntimeError("youtube_token.json not found. Run auth script.")

    credentials = Credentials.from_authorized_user_file(
        token_path,
        scopes=SCOPES
    )

    try:
        if not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                logger.info("🔄 Refreshing YouTube token...")

                credentials.refresh(Request())

                # 🔥 Persist refreshed token (CRITICAL FIX)
                with open(token_path, "w") as token:
                    token.write(credentials.to_json())

                logger.info("✅ Token refreshed and saved")

            else:
                raise RuntimeError("Invalid YouTube credentials. Re-auth required.")

    except Exception as e:
        logger.error("❌ Failed to refresh YouTube token", exc_info=True)
        raise RuntimeError("YouTube auth failed") from e

    return build("youtube", "v3", credentials=credentials)


# ---------------------------------------------------------
# UPLOAD VIDEO
# ---------------------------------------------------------
def upload_video(video, file_path: str) -> dict:
    """
    Uploads video to YouTube (production-grade)
    Returns: { youtube_id, youtube_url }
    """

    logger.info(
        f"📺 YouTube upload started | video_id={video.id} | file={file_path}"
    )

    if not os.path.exists(file_path):
        raise RuntimeError(f"File not found for upload: {file_path}")

    youtube = get_youtube_client()

    # -----------------------------------------------------
    # 🔥 METADATA OPTIMIZATION (PRODUCTION)
    # -----------------------------------------------------
    base_title = (
        video.script.title
        if getattr(video, "script", None) and video.script.title
        else f"AI Video #{video.id}"
    )

    title = base_title[:70]

    base_description = (
        video.script.description
        if getattr(video, "script", None) and video.script.description
        else ""
    )

    description = f"""{base_title}

{base_description}

#shorts #ai #viral #trending
"""

    tags = []
    if getattr(video, "script", None):
        if hasattr(video.script, "tags") and video.script.tags:
            try:
                tags = list(video.script.tags)
            except Exception:
                tags = []

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": YOUTUBE_CATEGORY_ID,
            "tags": tags,
        },
        "status": {
            "privacyStatus": "unlisted",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        file_path,
        chunksize=-1,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    retries = 0
    max_retries = 3

    while response is None:
        try:
            status, response = request.next_chunk()

            if status:
                logger.info(
                    f"📤 Upload progress: {int(status.progress() * 100)}%"
                )

        except HttpError as e:
            retries += 1

            logger.warning(
                f"⚠️ YouTube upload retry {retries}/{max_retries} | error={e}"
            )

            if retries > max_retries:
                logger.error("❌ YouTube upload failed after retries", exc_info=True)
                raise

            sleep_time = 2 ** retries
            logger.info(f"⏳ Retrying in {sleep_time}s...")
            time.sleep(sleep_time)

        except Exception as e:
            retries += 1
            logger.error("❌ Unexpected upload error", exc_info=True)

            if retries > max_retries:
                raise

            sleep_time = 2 ** retries
            time.sleep(sleep_time)

    video_id = response.get("id")

    if not video_id:
        raise RuntimeError("YouTube upload failed: No video ID returned")

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"

    logger.info(
        f"✅ YouTube upload success | video_id={video.id} | youtube_id={video_id}"
    )

    return {
        "youtube_id": video_id,
        "youtube_url": youtube_url,
    }


def upload_thumbnail(youtube_id: str, thumbnail_path: str):
    """
    Upload thumbnail to an existing YouTube video
    """

    logger.info(
        f"🖼 Uploading thumbnail | youtube_id={youtube_id} | file={thumbnail_path}"
    )

    if not os.path.exists(thumbnail_path):
        logger.warning("⚠️ Thumbnail not found, skipping")
        return False

    youtube = get_youtube_client()

    try:
        request = youtube.thumbnails().set(
            videoId=youtube_id,
            media_body=MediaFileUpload(thumbnail_path)
        )

        request.execute()

        logger.info(f"✅ Thumbnail uploaded | youtube_id={youtube_id}")
        return True

    except HttpError:
        logger.error("❌ Thumbnail upload failed", exc_info=True)
        return False


def upload_captions(youtube_id: str, srt_path: str):
    """
    Upload captions (SRT) to YouTube video
    """

    logger.info(
        f"📝 Uploading captions | youtube_id={youtube_id} | file={srt_path}"
    )

    if not os.path.exists(srt_path):
        logger.warning("⚠️ SRT file not found, skipping captions")
        return False

    youtube = get_youtube_client()

    try:
        request = youtube.captions().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": youtube_id,
                    "language": "en",
                    "name": "English",
                    "isDraft": False
                }
            },
            media_body=MediaFileUpload(srt_path)
        )

        request.execute()

        logger.info(f"✅ Captions uploaded | youtube_id={youtube_id}")
        return True

    except HttpError as e:
        if "insufficientPermissions" in str(e):
            logger.warning("⚠️ Captions API not allowed → skipping")
            return False

        logger.error("❌ Caption upload failed", exc_info=True)
        return False


# ---------------------------------------------------------
# 🚀 PUBLISH VIDEO (UNLISTED → PUBLIC)
# ---------------------------------------------------------
def publish_video(video_id: int):
    """
    Switch video from UNLISTED → PUBLIC
    """

    from app.db.database import SessionLocal
    from app.models.video import Video
    from app.models.video_platform_status import VideoPlatformStatus

    logger.info(f"🚀 Publishing video | video_id={video_id}")

    db = SessionLocal()

    try:
        video = db.get(Video, video_id)
        approval_status = getattr(
            getattr(video, "approval_status", None),
            "value",
            getattr(video, "approval_status", None),
        )
        if not video or approval_status != "approved":
            raise RuntimeError("Publishing blocked: video is not approved")

        status = (
            db.query(VideoPlatformStatus)
            .filter(
                VideoPlatformStatus.video_id == video_id,
                VideoPlatformStatus.status == "success"
            )
            .order_by(VideoPlatformStatus.created_at.desc())
            .first()
        )

        if not status or not status.uploaded_url:
            raise RuntimeError("YouTube video not found in platform status")

        youtube_id = status.uploaded_url.split("v=")[-1]

        youtube = get_youtube_client()

        request = youtube.videos().update(
            part="status",
            body={
                "id": youtube_id,
                "status": {
                    "privacyStatus": "public"
                }
            }
        )

        request.execute()

        logger.info(f"✅ Video published successfully | youtube_id={youtube_id}")
        return True

    except Exception:
        logger.error("❌ Failed to publish video", exc_info=True)
        raise

    finally:
        db.close()
