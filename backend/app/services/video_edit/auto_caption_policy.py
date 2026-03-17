import random
from app.services.video_edit.caption_styles import STYLES

def choose_caption_style(category_name: str) -> str:
    """
    Automatically select caption style based on category name.

    This function is intentionally lightweight and rule-based.
    It can later be replaced by ML/AI-based styling if needed.
    """

    if not category_name:
        return "sleek"

    c = category_name.lower().strip()

    # ---------------------------------------------------------
    # Horror / Scary
    # ---------------------------------------------------------
    if any(k in c for k in ["horror", "scary", "creepy", "ghost"]):
        return "red_highlight"

    # ---------------------------------------------------------
    # Motivation / Inspiration
    # ---------------------------------------------------------
    if any(k in c for k in ["motivation", "inspiration", "success"]):
        return "majestic"

    # ---------------------------------------------------------
    # Story / Storytelling
    # ---------------------------------------------------------
    if any(k in c for k in ["story", "storytelling", "narrative"]):
        return "bold_stroke"

    # ---------------------------------------------------------
    # Viral / Shorts / Social style (TikTok / MrBeast captions)
    # ---------------------------------------------------------
    if any(k in c for k in ["viral", "shorts", "reels", "trending"]):
        return "beast"

    # ---------------------------------------------------------
    # Education / Facts / Knowledge
    # ---------------------------------------------------------
    if any(k in c for k in ["facts", "education", "science", "history"]):
        return "sleek"

    # ---------------------------------------------------------
    # ASMR / Calm / Relax
    # ---------------------------------------------------------
    if any(k in c for k in ["asmr", "relax", "calm", "sleep"]):
        return "sleek"

    # ---------------------------------------------------------
    # Default fallback
    # ---------------------------------------------------------
    return "sleek"


def random_style():
    """
    Randomly choose a caption style from available styles.
    """
    styles = list(STYLES.keys())

    if not styles:
        return "sleek"  # safe fallback

    return random.choice(styles)