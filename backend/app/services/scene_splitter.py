import os
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any

# ✅ SINGLE SOURCE OF TRUTH
from app.utils.asset_paths import scenes_dir

WORDS_PER_SECOND = 2.2  # realistic narration speed

# ---------------------------------------------------------
# Emotion keyword map
# ---------------------------------------------------------
EMOTION_KEYWORDS = {
    "horror": {
        "keywords": [
            "monster", "ghost", "blood", "creature",
            "demon", "evil", "darkness", "haunted",
            "shadow", "terror", "scream"
        ],
        "verbs": [
            "lurks", "stalks", "emerges", "appears"
        ],
        "weight": 2.0
    },

    "suspense": {
        "keywords": [
            "creak", "whisper", "slowly", "tension",
            "waiting", "silence", "watching",
            "unknown", "suddenly"
        ],
        "verbs": [
            "moves", "opens", "approaches"
        ],
        "weight": 1.6
    },

    "action": {
        "keywords": [
            "fight", "battle", "explodes", "crash",
            "attack", "chase"
        ],
        "verbs": [
            "runs", "jumps", "dodges", "strikes",
            "charges", "smashes"
        ],
        "weight": 1.8
    },

    "calm": {
        "keywords": [
            "sunset", "breeze", "gentle", "peaceful",
            "quiet", "soft", "nature"
        ],
        "verbs": [
            "flows", "rests", "drifts"
        ],
        "weight": 1.2
    },

    "dramatic": {
        "keywords": [
            "dramatic", "intense", "reveal",
            "shocking", "powerful"
        ],
        "verbs": [
            "reveals", "confronts", "declares"
        ],
        "weight": 1.4
    }
}

# ---------------------------------------------------------
# Emotion detector
# ---------------------------------------------------------
def _detect_emotion(text: str, default: str = "neutral") -> str:
    if not text:
        return default

    text_lower = text.lower()

    scores = {}

    for emotion, data in EMOTION_KEYWORDS.items():
        score = 0
        # keyword match
        for word in data.get("keywords", []):
            if word in text_lower:
                score += 2

        # verb match
        for verb in data.get("verbs", []):
            if verb in text_lower:
                score += 1

        # punctuation intensity
        if "!" in text and emotion in ["action", "horror"]:
            score += 1

        # sentence length heuristic
        if len(text.split()) > 12 and emotion == "dramatic":
            score += 1

        # apply weight
        score *= data.get("weight", 1)

        scores[emotion] = score

    if not scores:
        return default

    best_emotion = max(scores, key=scores.get)

    if scores[best_emotion] <= 0:
        return default

    return best_emotion

# ---------------------------------------------------------
# Safe JSON loader
# ---------------------------------------------------------
def _safe_load_json(value) -> Dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except Exception:
        return {}

# ---------------------------------------------------------
# Build unified prompt_json (LOCKED)
# ---------------------------------------------------------
def _build_prompt_json(script) -> Dict[str, Any]:
    parsed = _safe_load_json(script.parsed_json)

    return {
        "title": script.title,
        "description": (
            parsed.get("description")
            or getattr(script, "description", "")
            or ""
        ),
        "style": parsed.get("style", {}),
        "visual": parsed.get("visual", {}),
        "audio": parsed.get("audio", {}),
        "generation": parsed.get("generation", {}),
        "language": getattr(script, "language", "English"),
        "tone": getattr(script, "tone", "neutral"),
    }

# ---------------------------------------------------------
# Semantic text splitter (NON-ASMR)
# ---------------------------------------------------------
def _semantic_split(content: str) -> List[str]:
    if not content or not content.strip():
        return []

    chunks = re.split(r"[.!?]\s+", content.replace("\n", " "))
    chunks = [c.strip() for c in chunks if len(c.strip()) >= 20]

    return chunks or [content.strip()]

# ---------------------------------------------------------
# Build narrative scenes (LOCKED SCHEMA)
# ---------------------------------------------------------
def _build_semantic_scenes(
    chunks: List[str],
    visual_env: str,
    tone: str,
) -> List[Dict[str, Any]]:
    scenes = []

    for idx, narration in enumerate(chunks, start=1):
        word_count = len(narration.split())
        duration_sec = max(4, int(word_count / WORDS_PER_SECOND))

        # -------------------------------------------------
        # NEW: Emotion detection
        # -------------------------------------------------
        detected_emotion = _detect_emotion(
            narration,
            default=tone or "neutral"
        )

        scenes.append({
            "index": idx,
            "narration": narration,
            "duration_sec": duration_sec,
            # upgraded emotion logic
            "emotion": detected_emotion,
            "pacing": "steady",
            "visual_prompt": f"{visual_env}, cinematic framing, scene {idx}",
        })

    return scenes

# ---------------------------------------------------------
# Build ASMR scenes (LOCKED SCHEMA)
# ---------------------------------------------------------
def _build_asmr_scenes(
    voice_length_seconds: int,
    visual_env: str,
) -> List[Dict[str, Any]]:
    SCENE_DURATION = 6
    num_scenes = max(1, voice_length_seconds // SCENE_DURATION)

    variations = [
        "slow zoom",
        "camera drift",
        "macro texture",
        "ambient stillness",
    ]

    scenes = []
    for idx in range(1, num_scenes + 1):
        scenes.append({
            "index": idx,
            "narration": "",
            "duration_sec": SCENE_DURATION,
            "emotion": "calm",
            "pacing": "slow",
            "visual_prompt": (
                f"{visual_env}, {variations[(idx - 1) % len(variations)]}"
            ),
        })

    return scenes

# ---------------------------------------------------------
# MAIN ENTRY (LOCKED)
# ---------------------------------------------------------
def split_into_scenes(script, voice_length_seconds: int):
    """
    Deterministic scene splitter.

    Returns:
    - scenes (LOCKED schema list)
    - manifest_path (str)
    """

    content = script.content or ""

    # ✅ CORRECT CATEGORY RESOLUTION
    category_name = ""
    if getattr(script, "category", None) and script.category.name:
        category_name = script.category.name.lower()

    is_asmr = "asmr" in category_name

    prompt_json = _build_prompt_json(script)

    visual_env = (
        prompt_json.get("visual", {}).get("environment")
        or "cinematic environment"
    )

    tone = (
        prompt_json.get("generation", {}).get("tone")
        or getattr(script, "tone", "neutral")
    )

    # -------------------------------------------------
    # Scene generation
    # -------------------------------------------------
    if is_asmr:
        scenes = _build_asmr_scenes(
            voice_length_seconds=voice_length_seconds,
            visual_env=visual_env,
        )
    else:
        chunks = _semantic_split(content)
        scenes = _build_semantic_scenes(
            chunks=chunks,
            visual_env=visual_env,
            tone=tone,
        )

    # -------------------------------------------------
    # ENV LIMIT
    # -------------------------------------------------
    env = os.getenv("AIYT_ENV", "DEV").upper()
    max_scenes = 5 if env == "DEV" else 8
    scenes = scenes[:max_scenes]

    # -------------------------------------------------
    # MANIFEST WRITE (script-scoped)
    # -------------------------------------------------
    folder = scenes_dir(script.id, video_id=0)
    os.makedirs(folder, exist_ok=True)

    manifest_path = os.path.join(folder, "manifest.json")

    manifest = {
        "script_id": script.id,
        "category": script.category.name if script.category else "Unknown",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "env": env,
        "scene_count": len(scenes),
        "scenes": scenes,
        "prompt_json": prompt_json,
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return scenes, manifest_path
