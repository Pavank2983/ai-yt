import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any

# Hardcoded category map
CATEGORY_MAP = {
    1: "Sci-Fi",
    2: "Horror",
    3: "Tech",
    4: "ASMR",
    5: "Storytelling",
}

# ---------------------------------------------------------
# Folder helper (patched in tests)
# ---------------------------------------------------------
def _ensure_scene_folder(script_id: int) -> str:
    base = f"assets/videos/scenes/{script_id}"
    os.makedirs(base, exist_ok=True)
    return base

# ---------------------------------------------------------
# Simple prompt_json builder (internal)
# ---------------------------------------------------------
def _build_prompt_json(script) -> Dict[str, Any]:
    return {
        "title": script.title,
        "description": script.description or "",
        "content": script.content or "",
        "tone": getattr(script, "tone", "default"),
        "language": getattr(script, "language", "English"),
        "keywords": [],
    }

# ---------------------------------------------------------
# Split text into rough semantic chunks (fallback mode)
# ---------------------------------------------------------
def _semantic_split(content: str) -> List[str]:
    if not content.strip():
        return [""]

    # Basic splitter using punctuation
    chunks = re.split(r"[.!?]\s+", content)
    chunks = [c.strip() for c in chunks if c.strip()]

    # Guarantee at least 1
    return chunks if chunks else [""]

# ---------------------------------------------------------
# Build semantic scene descriptors
# ---------------------------------------------------------
def _build_semantic_scenes(chunks: List[str]) -> List[Dict[str, Any]]:
    scenes = []
    for i, chunk in enumerate(chunks, start=1):
        scenes.append({
            "index": i,
            "title": f"Scene {i}",
            "summary": chunk[:120],
            "emotion": "neutral",
            "prompt": {
                "scene_title": f"Scene {i}",
                "description": chunk,
            }
        })
    return scenes

# ---------------------------------------------------------
# Build ASMR duration-based scenes
# ---------------------------------------------------------
def _build_asmr_scenes(voice_length_seconds: int) -> List[Dict[str, Any]]:
    num_scenes = max(1, voice_length_seconds // 6)

    variations = ["zoom_in", "camera_sweep", "ambient"]
    scenes = []

    for i in range(1, num_scenes + 1):
        scenes.append({
            "index": i,
            "variation": variations[(i - 1) % len(variations)],
            "prompt": {
                "scene": i,
                "style": "asmr",
                "direction": variations[(i - 1) % len(variations)],
            }
        })

    return scenes

# ---------------------------------------------------------
# Main Scene Splitter
# ---------------------------------------------------------
def split_into_scenes(script, voice_length_seconds):
    """
    Unified simplified API:
    - script: Script-like object
    - voice_length_seconds: total TTS duration
    """

    content = script.content or ""
    category_name = CATEGORY_MAP.get(script.category_id, "Unknown")

    # Auto-build prompt JSON internally
    prompt_json = _build_prompt_json(script)

    # ---------------------------------------------
    # ASMR path
    # ---------------------------------------------
    if category_name == "ASMR":
        scenes = _build_asmr_scenes(voice_length_seconds)

    else:
        # Semantic fallback mode (no OpenAI)
        chunks = _semantic_split(content)
        scenes = _build_semantic_scenes(chunks)

    # ---------------------------------------------
    # DEV/PROD scene limit
    # ---------------------------------------------
    env = os.getenv("AIYT_ENV", "DEV").upper()
    max_scenes = 5 if env == "DEV" else 7
    scenes = scenes[:max_scenes]

    # ---------------------------------------------
    # Write manifest
    # ---------------------------------------------
    folder = _ensure_scene_folder(script.id)
    manifest_path = os.path.join(folder, "manifest.json")

    manifest = {
        "script_id": script.id,
        "category": category_name,
        "generated_at": datetime.utcnow().isoformat(),
        "scenes": scenes,
        "prompt_json": prompt_json,
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return scenes, manifest_path
