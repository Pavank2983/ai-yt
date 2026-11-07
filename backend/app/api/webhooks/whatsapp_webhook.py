"""WhatsApp approval webhook handlers.

The webhook is deliberately defensive: Meta's signature is checked before
the body is parsed, the sender must be the configured administrator, and the
approval transition is committed together with any upload jobs.
"""

import hashlib
import hmac
import json
import logging
import os
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app.db.database import SessionLocal
from app.models.approval_token import ApprovalAction, ApprovalToken
from app.models.platform import Platform
from app.models.video import Video
from app.models.video_job import JobMode, JobStatus, VideoJob
from app.models.video_platform_status import PlatformUploadStatus, VideoPlatformStatus
from app.services.approval.approval_service import ApprovalError, process_approval_token


router = APIRouter()
logger = logging.getLogger("whatsapp_service")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler("logs/whatsapp_service.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)


# There are intentionally no development fallbacks for security settings.
VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")
META_APP_SECRET = os.getenv("META_APP_SECRET")
ADMIN_PHONE = os.getenv("ADMIN_PHONE")


def _verify_signature(
    raw_body: bytes,
    signature_header: str | None,
    app_secret: str | None = META_APP_SECRET,
) -> bool:
    """Validate Meta's X-Hub-Signature-256 against the raw request body."""

    if not app_secret or not signature_header:
        return False
    if not re.fullmatch(r"sha256=[0-9a-fA-F]{64}", signature_header):
        return False

    expected = hmac.new(
        app_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header[7:])


def _normalize_phone(value: str | None) -> str:
    return "".join(character for character in str(value or "") if character.isdigit())


def _is_authorized_sender(
    sender: str | None,
    admin_phone: str | None = ADMIN_PHONE,
) -> bool:
    configured = _normalize_phone(admin_phone)
    actual = _normalize_phone(sender)
    return bool(configured and actual and hmac.compare_digest(actual, configured))


def _action_value(action: object) -> str:
    return str(getattr(action, "value", action))


def _enqueue_upload_jobs(db, video: Video, platforms: list[Platform]) -> None:
    """Create one status row and one upload job per platform, idempotently."""

    existing_jobs = (
        db.query(VideoJob)
        .filter(VideoJob.video_id == video.id, VideoJob.provider == "UPLOAD")
        .all()
    )
    existing_platforms: set[str] = set()
    for job in existing_jobs:
        try:
            metadata = json.loads(job.meta or "{}")
        except (TypeError, ValueError):
            metadata = {}
        platform_name = metadata.get("platform")
        if platform_name:
            existing_platforms.add(str(platform_name).lower())

    now = datetime.now(timezone.utc)
    for platform in platforms:
        platform_name = str(platform.name).lower()

        status_exists = (
            db.query(VideoPlatformStatus)
            .filter(
                VideoPlatformStatus.video_id == video.id,
                VideoPlatformStatus.platform_id == platform.id,
            )
            .first()
        )
        if status_exists is None:
            db.add(
                VideoPlatformStatus(
                    video_id=video.id,
                    platform_id=platform.id,
                    status=PlatformUploadStatus.pending,
                    created_at=now,
                    updated_at=now,
                )
            )

        if platform_name in existing_platforms:
            continue

        db.add(
            VideoJob(
                script_id=video.script_id,
                video_id=video.id,
                is_tts=False,
                provider="UPLOAD",
                provider_tier="standard",
                mode=JobMode.video_api,
                status=JobStatus.queued,
                created_at=now,
                meta=json.dumps({"platform": platform_name}),
            )
        )
        existing_platforms.add(platform_name)


@router.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """Handle Meta's subscription verification challenge."""

    params = request.query_params
    hub_mode = params.get("hub.mode")
    hub_verify_token = params.get("hub.verify_token")
    hub_challenge = params.get("hub.challenge")

    if hub_mode == "subscribe" and VERIFY_TOKEN and hmac.compare_digest(
        hub_verify_token or "", VERIFY_TOKEN
    ):
        logger.info("WhatsApp webhook verification succeeded")
        return PlainTextResponse(content=hub_challenge or "")

    logger.warning("WhatsApp webhook verification rejected")
    status_code = 503 if not VERIFY_TOKEN else 403
    return JSONResponse(
        status_code=status_code,
        content={"error": "verification failed"},
    )


@router.post("/webhook/whatsapp")
async def receive_webhook(request: Request):
    """Process signed WhatsApp approval button deliveries."""

    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not _verify_signature(raw_body, signature):
        logger.warning("WhatsApp webhook rejected: invalid signature")
        return JSONResponse(status_code=403, content={"status": "invalid_signature"})

    try:
        data = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("WhatsApp webhook rejected: malformed JSON")
        return JSONResponse(status_code=400, content={"status": "invalid_json"})

    try:
        entry = data.get("entry", [])
        if not entry:
            return {"status": "ignored"}

        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "ignored"}

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return {"status": "no_messages"}

        message = messages[0]
        if not ADMIN_PHONE:
            logger.error("WhatsApp webhook rejected: administrator phone is not configured")
            return JSONResponse(status_code=503, content={"status": "not_configured"})

        # The sender is taken from the signed message object, never from the
        # contacts/display-name fields supplied elsewhere in the payload.
        if not _is_authorized_sender(message.get("from")):
            logger.warning("WhatsApp webhook rejected: unauthorized sender")
            return JSONResponse(status_code=403, content={"status": "unauthorized_sender"})

        message_type = message.get("type")
        payload = None
        if message_type == "interactive":
            payload = message.get("interactive", {}).get("button_reply", {}).get("id")
        elif message_type == "button":
            payload = message.get("button", {}).get("payload")
        else:
            return {"status": "ignored"}

        if not payload:
            logger.warning("WhatsApp approval message had no action payload")
            return {"status": "no_payload"}

        db = SessionLocal()
        try:
            token = (
                db.query(ApprovalToken)
                .filter(ApprovalToken.token == payload)
                .first()
            )
            if not token:
                logger.warning("WhatsApp approval token was not found")
                return {"status": "invalid_token"}

            action = _action_value(token.action)
            platforms: list[Platform] = []
            if action == ApprovalAction.approve.value:
                platforms = db.query(Platform).filter(Platform.enabled.is_(True)).all()
                if not platforms:
                    logger.warning("WhatsApp approval deferred: no enabled platforms")
                    return {"status": "no_platforms"}

            try:
                video = process_approval_token(db, token, commit=False)
            except ApprovalError as error:
                db.rollback()
                result_by_error = {
                    "Token already used": "token_used",
                    "Token expired": "token_expired",
                    "Video not found": "video_not_found",
                    "Video already processed": "already_processed",
                }
                return {"status": result_by_error.get(str(error), "invalid_token")}

            if action == ApprovalAction.approve.value:
                video.status = "publishing"
                _enqueue_upload_jobs(db, video, platforms)

            # Token consumption, approval state and publishing work are one
            # transaction. A rollback therefore leaves the token reusable.
            db.commit()
            logger.info("WhatsApp approval processed | action=%s", action)
            return {"status": "processed"}
        except Exception as error:
            db.rollback()
            logger.error(
                "WhatsApp webhook processing failed | exception=%s",
                type(error).__name__,
            )
            return JSONResponse(status_code=500, content={"status": "error"})
        finally:
            db.close()
    except Exception as error:
        logger.error(
            "WhatsApp webhook payload handling failed | exception=%s",
            type(error).__name__,
        )
        return JSONResponse(status_code=500, content={"status": "error"})
