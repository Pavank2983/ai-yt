import os
import logging
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------
# Use the same logger as thumbnail_engine
# ------------------------------------------------------------
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


FONT_PATH = "assets/fonts/KomikaAxis.ttf"


def _short_title(title: str) -> str:
    """
    Convert long title into thumbnail text.
    """

    words = title.upper().split()

    if len(words) <= 4:
        return " ".join(words)

    return " ".join(words[:4])


def add_thumbnail_text(image_path: str, title: str, output_path: str):

    if not os.path.exists(image_path):
        raise RuntimeError(f"Image not found: {image_path}")

    text = _short_title(title)

    logger.info("[text-overlay] 📝 Overlay text → %s", text)

    img = Image.open(image_path).convert("RGB")

    draw = ImageDraw.Draw(img)

    width, height = img.size

    font_size = int(width * 0.08)

    try:
        font = ImageFont.truetype(FONT_PATH, font_size)

    except Exception as e:

        logger.warning(
            "[text-overlay] ⚠ Font load failed → using default font | %s",
            str(e)
        )

        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)

    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (width - text_w) / 2
    y = height * 0.75

    # ------------------------------------------------
    # Text shadow
    # ------------------------------------------------
    draw.text(
        (x + 4, y + 4),
        text,
        font=font,
        fill="black"
    )

    # ------------------------------------------------
    # Main text
    # ------------------------------------------------
    draw.text(
        (x, y),
        text,
        font=font,
        fill="white"
    )

    # ------------------------------------------------
    # Ensure output directory exists
    # ------------------------------------------------
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    img.save(output_path, "JPEG", quality=95)

    logger.info(
        "[text-overlay] 🏁 Thumbnail saved → %s",
        output_path
    )

    return output_path