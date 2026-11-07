import random, os
import logging
from app.services.video_edit.caption_styles import STYLES

logger = logging.getLogger("subtitle_engine")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/subtitle_engine.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

# ---------------------------------------------------------
# 🔍 Safe style validator
# ---------------------------------------------------------
def _safe_style(style: str) -> str:
    """
    Ensures the returned style exists in STYLES.
    Fallback → sleek
    """
    if style in STYLES:
        return style

    logger.warning(f"⚠ Caption style '{style}' not found → fallback to 'sleek'")
    return "sleek"


# ---------------------------------------------------------
# 🎯 Rule-based style selection
# ---------------------------------------------------------
def choose_caption_style(category_name: str) -> str:
    """
    Automatically select caption style based on category.

    Lightweight rule engine (fast, deterministic).
    """

    if not category_name:
        return "sleek"

    c = category_name.lower().strip()

    # ---------------------------------------------------------
    # Horror / Scary
    # ---------------------------------------------------------
    if any(k in c for k in ["horror", "scary", "creepy", "ghost"]):
        return _safe_style("red_highlight")

    # ---------------------------------------------------------
    # Motivation / Inspiration
    # ---------------------------------------------------------
    if any(k in c for k in ["motivation", "inspiration", "success"]):
        return _safe_style("majestic")

    # ---------------------------------------------------------
    # Story / Storytelling (BEST for your content)
    # ---------------------------------------------------------
    if any(k in c for k in ["story", "storytelling", "narrative"]):
        return _safe_style("bold_stroke")

    # ---------------------------------------------------------
    # Viral / Shorts / Social (HIGH ENGAGEMENT)
    # ---------------------------------------------------------
    if any(k in c for k in ["viral", "shorts", "reels", "trending"]):
        return _safe_style("beast")

    # ---------------------------------------------------------
    # Sci-Fi / Space (🔥 YOUR NICHE)
    # ---------------------------------------------------------
    if any(k in c for k in ["sci", "space", "alien", "future", "ai"]):
        return _safe_style("bold_stroke")

    # ---------------------------------------------------------
    # Education / Facts
    # ---------------------------------------------------------
    if any(k in c for k in ["facts", "education", "science", "history"]):
        return _safe_style("sleek")

    # ---------------------------------------------------------
    # ASMR / Calm
    # ---------------------------------------------------------
    if any(k in c for k in ["asmr", "relax", "calm", "sleep"]):
        return _safe_style("sleek")

    # ---------------------------------------------------------
    # Default fallback
    # ---------------------------------------------------------
    return "sleek"


# ---------------------------------------------------------
# 🎲 Random style (safe)
# ---------------------------------------------------------
def random_style() -> str:
    """
    Randomly choose a caption style (safe fallback included)
    """

    styles = list(STYLES.keys())

    if not styles:
        logger.warning("⚠ No styles found → fallback to 'sleek'")
        return "sleek"

    return random.choice(styles)