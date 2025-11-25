import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.script import Script
from app.services.voice_generation_service import (
    generate_voice_for_script,
    generate_multivoice_for_script
)
from app.core.security import role_required
from datetime import datetime, UTC
import re

router = APIRouter()


@router.post("/voice/generate/{script_id}")
def generate_voice_endpoint(
    script_id: int,
    force_single: bool = Query(False, description="Force single narrator voice"),
    force_multi: bool = Query(False, description="Force multi-voice generation"),
    provider: str = Query(None, description="Optional: override TTS provider"),
    db: Session = Depends(get_db),
    current_user=Depends(role_required("editor"))
):
    """
    🎙️ Unified Voice Generation Endpoint

    Automatically decides between:
    - Single-voice generation (narration style)
    - Multi-voice generation (dialogue scripts)

    Detection based on content pattern:
        "Person 1: ..."
        "Narrator: ..."
        "Character A: ..."
    
    Frontend just calls this endpoint — backend handles detection & routing.

    Optional Query Params:
        ?force_single=true  → always use single narrator
        ?force_multi=true   → always use multi-voice mode
        ?provider=elevenlabs → override TTS provider
    """

    # Step 1️⃣ Fetch the script
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    if not script.content or script.content.strip() == "":
        raise HTTPException(status_code=400, detail="Script content is empty")

    content = script.content.strip()

    # Step 2️⃣ Detect dialogue pattern
    dialogue_pattern = r"([A-Za-z0-9\s]+):\s*(.+)"
    has_dialogue = bool(re.search(dialogue_pattern, content))

    FORCE_VOICE_TYPE = os.getenv("FORCE_VOICE_TYPE", "single").lower()

    # Step 3️⃣ Decide generation mode
    if force_single or FORCE_VOICE_TYPE == 'single':
        mode = "single"
    elif force_multi:
        mode = "multi"
    else:
        mode = "multi" if has_dialogue else "single"

    print(f"[INFO] Voice generation mode for Script {script_id}: {mode.upper()} (forced: {force_single or force_multi})")

    # Step 4️⃣ Perform voice generation
    try:
        if mode == "multi":
            result = generate_multivoice_for_script(db=db, script=script)
        else:
            result = generate_voice_for_script(db=db, script=script, provider=provider)

        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Voice generation failed"))

        # Step 5️⃣ Return unified response
        return {
            "success": True,
            "script_id": script.id,
            "mode": mode,
            "provider": result.get("provider", provider or "auto"),
            "voice_name": result.get("voice_name"),
            "duration": result.get("duration") or result.get("total_duration"),
            "file_path": result.get("file_path"),
            "merged_file": result.get("merged_file"),
            "segments": result.get("segments"),
            "message": result.get("message", "Voice generation completed"),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice generation failed: {str(e)}")
