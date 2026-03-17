import os
import requests
import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.video import Video
from app.models.approval_token import ApprovalToken


logger = logging.getLogger("whatsapp_service")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/whatsapp_service.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
ADMIN_PHONE = os.getenv("ADMIN_PHONE")
BASE_URL = os.getenv("BASE_URL")


def send_video_review_notification(db: Session, video: Video):
    """
    Sends WhatsApp template message to admin when a video is ready for review.
    """

    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_ID or not ADMIN_PHONE:
        raise RuntimeError("WhatsApp environment variables not configured")

    if not BASE_URL:
        raise RuntimeError("BASE_URL not configured")

    logger.info(
        "📲 Sending WhatsApp review notification | video_id=%s",
        video.id
    )

    # ------------------------------------------------
    # Resolve video URL (must be public for WhatsApp)
    # ------------------------------------------------
    video_url = video.file_url

    if not video_url:
        raise RuntimeError("Video file_url missing")

    video_url = video_url.replace("\\", "/")

    if not video_url.startswith("http"):
        video_url = f"{BASE_URL.rstrip('/')}/{video_url.lstrip('/')}"

    logger.info(
        "🎬 Video URL resolved | video_id=%s | url=%s",
        video.id,
        video_url
    )

    # ------------------------------------------------
    # Validate video URL accessibility
    # ------------------------------------------------
    try:

        check = requests.head(video_url, timeout=5)

        if check.status_code >= 400:
            raise RuntimeError(
                f"Video URL not publicly accessible: {video_url} "
                f"(status={check.status_code})"
            )

    except Exception as e:

        logger.error(
            "❌ Video URL validation failed | video_id=%s | url=%s",
            video.id,
            video_url
        )
        raise

    # ------------------------------------------------
    # Generate approval tokens
    # ------------------------------------------------
    approve_token = secrets.token_urlsafe(32)
    reject_token = secrets.token_urlsafe(32)

    approve_record = ApprovalToken(
        video_id=video.id,
        token=approve_token,
        action="approve",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        created_at=datetime.now(timezone.utc),
    )

    reject_record = ApprovalToken(
        video_id=video.id,
        token=reject_token,
        action="reject",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        created_at=datetime.now(timezone.utc),
    )

    db.add(approve_record)
    db.add(reject_record)
    db.commit()

    logger.info(
        "🔑 Approval tokens created | video_id=%s",
        video.id
    )

    # ------------------------------------------------
    # WhatsApp Template Payload
    # ------------------------------------------------
    url = f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": ADMIN_PHONE,
        "type": "template",
        "template": {
            "name": "video_approval",
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "video",
                            "video": {
                                "link": video_url
                            }
                        }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": str(video.id)
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "0",
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": approve_token
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "1",
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": reject_token
                        }
                    ]
                }
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:

        # ------------------------------------------------
        # Check local file size (WhatsApp limit ≈ 16MB)
        # ------------------------------------------------
        try:

            local_path = video.file_url.replace("\\", "/")

            if local_path.startswith("/"):
                local_path = local_path[1:]

            local_path = os.path.join(os.getcwd(), local_path)

            if os.path.exists(local_path):

                if os.path.getsize(local_path) > 16 * 1024 * 1024:
                    logger.warning(
                        "⚠ Video exceeds WhatsApp media limit (~16MB) | video_id=%s",
                        video.id
                    )

        except Exception as e:

            logger.warning(
                "Video size check skipped | video_id=%s | %s",
                video.id,
                str(e)
            )

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code >= 300:
            raise RuntimeError(
                f"WhatsApp send failed: {response.status_code} {response.text}"
            )

        data = response.json()

        message_id = data.get("messages", [{}])[0].get("id")

        logger.info(
            "✅ WhatsApp notification sent | video_id=%s | message_id=%s",
            video.id,
            message_id
        )

        return data

    except Exception as e:

        logger.error(
            "❌ WhatsApp notification failed | video_id=%s → %s",
            video.id,
            str(e),
            exc_info=True
        )

        raise