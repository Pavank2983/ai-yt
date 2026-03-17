from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
import logging, os

from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.models.approval_token import ApprovalToken
from app.models.video import Video

router = APIRouter()

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


# ------------------------------------------------
# CONFIG
# ------------------------------------------------
VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ai_video_webhook")


# ------------------------------------------------
# WEBHOOK VERIFICATION
# ------------------------------------------------
@router.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """
    WhatsApp webhook verification
    """

    params = request.query_params

    hub_mode = params.get("hub.mode")
    hub_verify_token = params.get("hub.verify_token")
    hub_challenge = params.get("hub.challenge")

    logger.info(
        "🔐 Webhook verification request | mode=%s token=%s",
        hub_mode,
        hub_verify_token
    )

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully")

        return PlainTextResponse(content=hub_challenge)

    logger.error("❌ Webhook verification failed")
    return {"error": "verification failed"}


# ------------------------------------------------
# RECEIVE WEBHOOK EVENTS
# ------------------------------------------------
@router.post("/webhook/whatsapp")
async def receive_webhook(request: Request):
    """
    Receives button responses from WhatsApp
    """

    try:

        data = await request.json()

        logger.info("📩 WhatsApp webhook received: %s", data)

        entry = data.get("entry", [])
        if not entry:
            return {"status": "ignored"}

        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "ignored"}

        value = changes[0].get("value", {})

        if "messages" not in value:
            return {"status": "no_messages"}

        message = value["messages"][0]

        message_type = message.get("type")

        logger.info("📨 Message type received: %s", message_type)

        payload = None

        # ------------------------------------------------
        # INTERACTIVE BUTTON RESPONSE (Cloud API)
        # ------------------------------------------------
        if message_type == "interactive":

            interactive = message.get("interactive", {})
            button_reply = interactive.get("button_reply", {})

            payload = button_reply.get("id")

            logger.info("🔘 Interactive button payload: %s", payload)

        # ------------------------------------------------
        # LEGACY BUTTON FORMAT
        # ------------------------------------------------
        elif message_type == "button":

            button = message.get("button", {})

            payload = button.get("payload")

            logger.info("🔘 Legacy button payload: %s", payload)

        else:
            return {"status": "ignored"}

        if not payload:
            logger.warning("⚠ No payload received from button")
            return {"status": "no_payload"}

        # ------------------------------------------------
        # TOKEN VALIDATION
        # ------------------------------------------------
        db = SessionLocal()

        try:

            token = (
                db.query(ApprovalToken)
                .filter(ApprovalToken.token == payload)
                .first()
            )

            if not token:
                logger.warning("⚠ Invalid approval token received")
                return {"status": "invalid_token"}

            if token.used_at:
                logger.warning("⚠ Token already used | video_id=%s", token.video_id)
                return {"status": "token_used"}

            expires_at = token.expires_at

            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at < datetime.now(timezone.utc):
                logger.warning("⚠ Token expired | video_id=%s", token.video_id)
                return {"status": "token_expired"}

            video = db.query(Video).get(token.video_id)

            if not video:
                logger.warning("⚠ Video not found | video_id=%s", token.video_id)
                return {"status": "video_not_found"}

            # ------------------------------------------------
            # APPROVE / REJECT ACTION
            # ------------------------------------------------
            if token.action == "approve":

                logger.info(
                    "✅ Video approved via WhatsApp | video_id=%s",
                    video.id
                )

                video.approval_status = "approved"

                # TODO: trigger publish worker

            elif token.action == "reject":

                logger.info(
                    "❌ Video rejected via WhatsApp | video_id=%s",
                    video.id
                )

                video.approval_status = "rejected"

                # TODO: trigger revision / edit pipeline

            token.used_at = datetime.now(timezone.utc)

            db.commit()

            return {"status": "processed"}

        finally:

            db.close()

    except Exception as e:

        logger.error(
            "❌ Webhook error: %s",
            str(e),
            exc_info=True
        )

        return {"status": "error"}