from typing import Dict
import os

from app.services.provider_health_service import is_provider_healthy
from app.db.database import SessionLocal


# ---------------------------------------------------------
# ENV
# ---------------------------------------------------------
AI_VIDEO_PROVIDER = os.getenv("AI_VIDEO_PROVIDER", "SILICONFLOW").upper()

IMAGE_MOTION_ENABLED = os.getenv("IMAGE_MOTION_ENABLED", "false").lower() == "true"
IMAGE_MOTION_MODE = os.getenv("IMAGE_MOTION_MODE", "disabled").lower()

def _load_allowed_providers():
    raw = os.getenv("AI_VIDEO_ALLOWED_PROVIDERS", "MINIMAX,SILICONFLOW")
    return {p.strip().upper() for p in raw.split(",") if p.strip()}

ALLOWED_PROVIDERS = _load_allowed_providers()


# ---------------------------------------------------------
# Cost Modes
# ---------------------------------------------------------
COST_MODE_PREMIUM = "premium"
COST_MODE_BALANCED = "balanced"
COST_MODE_AGGRESSIVE = "aggressive"

VALID_COST_MODES = {
    COST_MODE_PREMIUM,
    COST_MODE_BALANCED,
    COST_MODE_AGGRESSIVE,
}


# ---------------------------------------------------------
# Estimated Cost Map
# ---------------------------------------------------------
ESTIMATED_COSTS = {
    "MINIMAX": 0.50,
    "KLING": 0.30,
    "RUNWAY": 0.35,
    "SILICONFLOW": 0.15,
    "SORA": 0.60,
    "VEO": 0.55,
    "SYNTHETIC": 0.02,
}


# ---------------------------------------------------------
# Scene Classification
# ---------------------------------------------------------
def classify_scene(scene_index: int, total_scenes: int) -> str:

    if total_scenes <= 0:
        return "primary"

    if scene_index == 0:
        return "hook"

    if scene_index == total_scenes - 1:
        return "ending"

    if scene_index <= 2:
        return "primary"

    return "broll"


# ---------------------------------------------------------
# Downgrade Logic
# ---------------------------------------------------------
def downgrade_provider(current_tier: str) -> str:
    if current_tier == "premium":
        return "standard"
    if current_tier == "standard":
        return "cheap"
    return "cheap"


# ---------------------------------------------------------
# Provider Health-Aware Selector
# ---------------------------------------------------------
def _get_first_healthy_provider(preferred: str) -> str:

    db = SessionLocal()
    try:
        if preferred and preferred in ALLOWED_PROVIDERS:
            if is_provider_healthy(db, preferred):
                return preferred

        for p in ALLOWED_PROVIDERS:
            if is_provider_healthy(db, p):
                return p

        return preferred

    finally:
        db.close()


# ---------------------------------------------------------
# Tier → Provider Mapping
# ---------------------------------------------------------
def get_provider_for_tier(tier: str) -> str:

    primary = AI_VIDEO_PROVIDER

    if primary not in ALLOWED_PROVIDERS:
        primary = next(iter(ALLOWED_PROVIDERS))

    if primary == "MINIMAX":

        if tier == "premium":
            selected = "MINIMAX"
        elif tier in ("standard", "cheap"):
            selected = (
                "SILICONFLOW"
                if "SILICONFLOW" in ALLOWED_PROVIDERS
                else "MINIMAX"
            )
        else:
            selected = primary

    elif primary == "SILICONFLOW":
        selected = "SILICONFLOW"

    else:
        selected = primary

    selected = _get_first_healthy_provider(selected)

    return selected


# ---------------------------------------------------------
# Main Router
# ---------------------------------------------------------
def choose_provider(
    scene_index: int,
    total_scenes: int,
    attempts: int,
    category_name: str,
    cost_mode: str = COST_MODE_BALANCED,
) -> Dict:

    cost_mode = (cost_mode or COST_MODE_BALANCED).lower()
    if cost_mode not in VALID_COST_MODES:
        cost_mode = COST_MODE_BALANCED

    scene_type = classify_scene(scene_index, total_scenes)

    # -----------------------------------------------------
    # IMAGE MOTION OVERRIDE
    # -----------------------------------------------------
    if IMAGE_MOTION_ENABLED and IMAGE_MOTION_MODE != "disabled":

        if IMAGE_MOTION_MODE == "images_only":
            return {
                "provider": "SYNTHETIC",
                "provider_tier": "free",
                "mode": "image_motion",
                "estimated_cost": ESTIMATED_COSTS.get("SYNTHETIC", 0.02),
                "scene_type": scene_type,
            }

        if IMAGE_MOTION_MODE == "full":
            return {
                "provider": "SYNTHETIC",
                "provider_tier": "free",
                "mode": "image_motion",
                "estimated_cost": ESTIMATED_COSTS.get("SYNTHETIC", 0.02),
                "scene_type": scene_type,
            }

        if IMAGE_MOTION_MODE == "hybrid":
            if scene_type in ("broll", "ending"):
                return {
                    "provider": "SYNTHETIC",
                    "provider_tier": "free",
                    "mode": "image_motion",
                    "estimated_cost": ESTIMATED_COSTS.get("SYNTHETIC", 0.02),
                    "scene_type": scene_type,
                }

    # -----------------------------------------------------
    # Normal Video API Logic
    # -----------------------------------------------------
    if cost_mode == COST_MODE_PREMIUM:
        tier = "premium"
    elif cost_mode == COST_MODE_AGGRESSIVE:
        if scene_type == "hook":
            tier = "premium"
        elif scene_type == "primary":
            tier = "standard"
        else:
            tier = "cheap"
    else:
        if scene_type == "hook":
            tier = "premium"
        elif scene_type == "primary":
            tier = "standard"
        else:
            tier = "cheap"

    if attempts >= 1:
        tier = downgrade_provider(tier)

    provider = get_provider_for_tier(tier)
    mode = "video_api"

    # Aggressive synthetic fallback
    if cost_mode == COST_MODE_AGGRESSIVE and scene_type == "broll":
        provider = "SYNTHETIC"
        tier = "free"
        mode = "synthetic"

    if not provider:
        provider = AI_VIDEO_PROVIDER

    estimated_cost = ESTIMATED_COSTS.get(provider, 0.10)

    return {
        "provider": provider,
        "provider_tier": tier,
        "mode": mode,
        "estimated_cost": estimated_cost,
        "scene_type": scene_type,
    }