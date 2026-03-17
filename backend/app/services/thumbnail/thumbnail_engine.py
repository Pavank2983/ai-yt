import os
import logging
from pathlib import Path

from app.services.thumbnail.ai_thumbnail_generator import generate_ai_thumbnail
from app.services.thumbnail.frame_selector import extract_best_frame
from app.services.thumbnail.text_overlay import add_thumbnail_text

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
# CONFIG
# ============================================================

THUMBNAIL_AI_ENABLED = (
    os.getenv("THUMBNAIL_AI_ENABLED", "false").lower() == "true"
)


# ============================================================
# MAIN ENGINE
# ============================================================
def generate_thumbnail(
    video_path: str,
    script_title: str,
    output_dir: str,
):
    """
    Hybrid thumbnail generation engine.

    Order:
    1️⃣ AI generated thumbnail (optional)
    2️⃣ Frame selection fallback
    3️⃣ Text overlay
    """

    os.makedirs(output_dir, exist_ok=True)

    ai_thumb = os.path.join(output_dir, "thumb_ai.png")
    frame_thumb = os.path.join(output_dir, "thumb_frame.png")
    final_thumb = os.path.join(output_dir, "thumb_final.jpg")

    base_image = None

    # -----------------------------------------------------
    # 1️⃣ AI THUMBNAIL GENERATION (OPTIONAL)
    # -----------------------------------------------------
    if THUMBNAIL_AI_ENABLED:

        try:

            logger.info("🧠 Attempting AI thumbnail generation")

            generated = generate_ai_thumbnail(
                title=script_title,
                output_path=ai_thumb
            )

            if generated and os.path.exists(ai_thumb):

                logger.info("✅ AI thumbnail generated")

                base_image = ai_thumb

            else:

                raise RuntimeError("AI thumbnail returned invalid output")

        except Exception as e:

            logger.warning(
                "⚠ AI thumbnail failed → fallback to frame selector | %s",
                str(e)
            )

    else:

        logger.info("🧠 AI thumbnails disabled → using frame selector")

    # -----------------------------------------------------
    # 2️⃣ FRAME SELECTION FALLBACK
    # -----------------------------------------------------
    if base_image is None:

        try:

            logger.info("🎞 Extracting frame from video")

            frame = extract_best_frame(
                video_path=video_path,
                output_path=frame_thumb
            )

            if not frame or not os.path.exists(frame_thumb):
                raise RuntimeError("Frame extraction failed")

            logger.info("✅ Frame extracted")

            base_image = frame_thumb

        except Exception as e2:

            logger.error(
                "❌ Frame extraction failed | %s",
                str(e2)
            )

            raise RuntimeError("Thumbnail generation failed completely")

    # -----------------------------------------------------
    # 3️⃣ TEXT OVERLAY
    # -----------------------------------------------------
    try:

        logger.info("📝 Adding thumbnail text")

        add_thumbnail_text(
            image_path=base_image,
            title=script_title,
            output_path=final_thumb
        )

        if not os.path.exists(final_thumb):
            raise RuntimeError("Text overlay failed")

        logger.info("🏁 Thumbnail generated → %s", final_thumb)

        return final_thumb

    except Exception as e:

        logger.warning(
            "⚠ Text overlay failed → using base thumbnail | %s",
            str(e)
        )

        return base_image