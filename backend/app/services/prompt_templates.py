import json
from typing import Dict, Any

# =========================================================
# CATEGORY-BASED PROMPT PRESETS (PIPELINE AUTHORITY)
# =========================================================

CATEGORY_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "Sci-Fi": {
        "style": {
            "tone": "cinematic",
            "mood_keywords": ["mysterious", "cosmic", "epic", "futuristic"],
            "emotion": "awe",
            "pacing": "steady",
        },
        "visual": {
            "environment": "alien world, futuristic tech, holographic HUDs",
            "time": "deep space or dusk",
            "color_palette": "blue-violet, neon cyan, metallic silver",
            "camera_style": "slow orbit, sweeping cinematic shots",
            "lighting": "soft rim light, holographic reflections",
        },
        "audio": {
            "voice_style": "calm cinematic narration",
            "background_ambience": "soft sci-fi drones, cosmic hums",
            "pace": "medium",
            "intensity": "low",
        },
        "scene_defaults": {
            "avg_duration_sec": 4,
            "transition": "crossfade",
            "visual_density": "high",
        },
        "scripting_format": "narrative",
    },

    "Horror": {
        "style": {
            "tone": "dark",
            "mood_keywords": ["tense", "claustrophobic", "unnerving"],
            "emotion": "fear",
            "pacing": "slow buildup",
        },
        "visual": {
            "environment": "abandoned halls, foggy woods, dim rooms",
            "time": "late night",
            "color_palette": "dark greens, black shadows, crimson highlights",
            "camera_style": "handheld, slow zoom, tight framing",
            "lighting": "low light, flicker, harsh silhouettes",
        },
        "audio": {
            "voice_style": "whispery, tense, fearful",
            "background_ambience": "low rumbles, knocks, eerie drones",
            "pace": "slow",
            "intensity": "medium-high",
        },
        "scene_defaults": {
            "avg_duration_sec": 5,
            "transition": "fade",
            "visual_density": "medium",
        },
        "scripting_format": "narrative",
    },

    "Tech": {
        "style": {
            "tone": "reflective",
            "mood_keywords": ["clean", "analytical", "calm"],
            "emotion": "curiosity",
            "pacing": "balanced",
        },
        "visual": {
            "environment": "tech labs, neon interfaces, data visualization",
            "time": "timeless/artificial",
            "color_palette": "cool blues, whites, holographic purple",
            "camera_style": "smooth minimal tracking",
            "lighting": "digital glow",
        },
        "audio": {
            "voice_style": "calm documentary narration",
            "background_ambience": "light digital hum",
            "pace": "steady",
            "intensity": "low",
        },
        "scene_defaults": {
            "avg_duration_sec": 4,
            "transition": "cut",
            "visual_density": "medium",
        },
        "scripting_format": "narrative",
    },

    "ASMR": {
        "style": {
            "tone": "soft",
            "mood_keywords": ["cozy", "dreamlike", "relaxing"],
            "emotion": "calm",
            "pacing": "slow",
        },
        "visual": {
            "environment": "candle-lit room, close-up nature, glowing elements",
            "time": "night",
            "color_palette": "warm amber, soft beige, pastel blue",
            "camera_style": "slow drift, macro close-up",
            "lighting": "soft diffused glow",
        },
        "audio": {
            "voice_style": "whisper",
            "background_ambience": "soft wind, water, gentle chimes",
            "pace": "slow",
            "intensity": "very low",
        },
        "scene_defaults": {
            "avg_duration_sec": 6,
            "transition": "crossfade",
            "visual_density": "low",
        },
        "scripting_format": "asmr",
    },

    "Storytelling": {
        "style": {
            "tone": "narrative",
            "mood_keywords": ["emotional", "immersive"],
            "emotion": "engagement",
            "pacing": "smooth",
        },
        "visual": {
            "environment": "wide landscapes, thematic story scenes",
            "time": "varies",
            "color_palette": "thematic",
            "camera_style": "wide → medium → close-up",
            "lighting": "cinematic contrast",
        },
        "audio": {
            "voice_style": "warm storyteller",
            "background_ambience": "soft pads",
            "pace": "medium",
            "intensity": "low",
        },
        "scene_defaults": {
            "avg_duration_sec": 4,
            "transition": "crossfade",
            "visual_density": "medium",
        },
        "scripting_format": "narrative",
    },
}

# =========================================================
# BUILD UNIFIED PROMPT PAYLOAD (DB + PIPELINE SAFE)
# =========================================================

def build_prompt_json(
    category_name: str,
    title: str,
    content: str,
    tone: str | None = None,
    length: str = "short",
    language: str = "English",
) -> Dict[str, Any]:
    """
    Build a unified prompt payload.

    This JSON is stored in:
    - scripts.parsed_json
    - Used later for scene splitting
    - Used for TTS + video generation
    - Used for thumbnail & metadata generation
    """

    base = CATEGORY_TEMPLATES.get(
        category_name, CATEGORY_TEMPLATES["Storytelling"]
    )

    payload = {
        "title": title,
        "description": content[:400],
        "style": {
            **base["style"],
            "override_tone": tone or base["style"]["tone"],
        },
        "visual": base["visual"],
        "audio": base["audio"],
        "scene_defaults": base["scene_defaults"],
        "generation": {
            "length": length,
            "language": language,
            "tone": tone or base["style"]["tone"],
            "scripting_format": base["scripting_format"],
            "ai_pipeline": {
                "tts_enabled": True,
                "video_enabled": True,
                "auto_scene_split": True,
            },
        },
    }

    return payload


# ---------------------------------------------------------
# Helper: Serialize for DB
# ---------------------------------------------------------

def build_prompt_json_str(*args, **kwargs) -> str:
    """
    Convenience wrapper for DB storage.
    """
    return json.dumps(
        build_prompt_json(*args, **kwargs),
        ensure_ascii=False,
        indent=2,
    )
