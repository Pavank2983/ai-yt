import json

# --------------------------------------------
# CATEGORY-BASED PROMPT PRESETS
# --------------------------------------------

CATEGORY_TEMPLATES = {
    "Sci-Fi": {
        "style": {
            "tone": "cinematic",
            "mood_keywords": ["mysterious", "cosmic", "epic", "futuristic"],
            "emotion": "awe",
            "pacing": "steady"
        },
        "visual": {
            "environment": "alien world, futuristic tech, holographic HUDs",
            "time": "deep space or dusk",
            "color_palette": "blue-violet, neon cyan, metallic silver",
            "camera_style": "slow orbit, sweeping cinematic shots",
            "lighting": "soft rim light, holographic reflections"
        },
        "audio": {
            "voice_style": "calm cinematic narration",
            "background_ambience": "soft sci-fi drones, cosmic hums",
            "pace": "medium",
            "intensity": "low"
        },
        "scripting_format": "narrative"
    },
    "Horror": {
        "style": {
            "tone": "dark",
            "mood_keywords": ["tense", "claustrophobic", "unnerving"],
            "emotion": "fear",
            "pacing": "slow buildup"
        },
        "visual": {
            "environment": "abandoned halls, foggy woods, dim rooms",
            "time": "late night",
            "color_palette": "dark greens, black shadows, crimson highlights",
            "camera_style": "handheld, slow zoom, tight framing",
            "lighting": "low light, flicker, harsh silhouettes"
        },
        "audio": {
            "voice_style": "whispery, tense, fearful",
            "background_ambience": "low rumbles, knocks, eerie drones",
            "pace": "slow",
            "intensity": "medium-high"
        },
        "scripting_format": "narrative"
    },
    "Tech": {
        "style": {
            "tone": "reflective",
            "mood_keywords": ["clean", "analytical", "calm"],
            "emotion": "curiosity",
            "pacing": "balanced"
        },
        "visual": {
            "environment": "tech labs, neon interfaces, data visualization",
            "time": "timeless/artificial",
            "color_palette": "cool blues, whites, holographic purple",
            "camera_style": "smooth minimal tracking",
            "lighting": "digital glow"
        },
        "audio": {
            "voice_style": "calm documentary narration",
            "background_ambience": "light digital hum",
            "pace": "steady",
            "intensity": "low"
        },
        "scripting_format": "narrative"
    },
    "ASMR": {
        "style": {
            "tone": "soft",
            "mood_keywords": ["cozy", "dreamlike", "relaxing"],
            "emotion": "calm",
            "pacing": "slow"
        },
        "visual": {
            "environment": "candle-lit room, close-up nature, glowing elements",
            "time": "night",
            "color_palette": "warm amber, soft beige, pastel blue",
            "camera_style": "slow drift, macro close-up",
            "lighting": "soft diffused glow"
        },
        "audio": {
            "voice_style": "whisper",
            "background_ambience": "soft wind, water, gentle chimes",
            "pace": "slow",
            "intensity": "very low"
        },
        "scripting_format": "asmr"
    },
    "Storytelling": {
        "style": {
            "tone": "narrative",
            "mood_keywords": ["emotional", "immersive"],
            "emotion": "engagement",
            "pacing": "smooth"
        },
        "visual": {
            "environment": "wide landscapes, thematic story scenes",
            "time": "varies",
            "color_palette": "thematic",
            "camera_style": "wide → medium → close-up",
            "lighting": "cinematic contrast"
        },
        "audio": {
            "voice_style": "warm storyteller",
            "background_ambience": "soft pads",
            "pace": "medium",
            "intensity": "low"
        },
        "scripting_format": "narrative"
    }
}

# ---------------------------------------------------------
# Function: Build Unified Prompt JSON
# ---------------------------------------------------------

def build_prompt_json(category_name, title, content, tone, length="short", language="English"):
    """
    Creates a full prompt JSON package for script generation,
    scene generation, and multi-scene processing.
    """

    base = CATEGORY_TEMPLATES.get(category_name, CATEGORY_TEMPLATES["Storytelling"])

    payload = {
        "title": title,
        "description": content[:400],  # short summary for metadata
        "style": base["style"],
        "visual": base["visual"],
        "audio": base["audio"],
        "generation": {
            "length": length,
            "language": language,
            "tone": tone,
            "scripting_format": base.get("scripting_format", "narrative"),
        }
    }

    return json.dumps(payload, ensure_ascii=False, indent=2)
