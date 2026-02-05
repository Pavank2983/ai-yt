from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.core.security import role_required
from app.models.script import Script
from app.schemas.script import ScriptCreate, ScriptResponse
from app.services.script_service import create_script
from app.services.script_bulk_service import bulk_generate_scripts
from app.models.video import Video
from app.services.orchestrator.video_orchestrator import VideoOrchestrator


from app.services.scene_splitter import split_into_scenes
import math

import openai

router = APIRouter(prefix="/scripts")


# =====================================================
# Helper: human-readable timestamps
# =====================================================

def humanize_time(dt: datetime | None) -> str:
    if not dt:
        return "-"

    diff = datetime.utcnow() - dt
    seconds = diff.total_seconds()
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24

    if days >= 1:
        return f"{int(days)} days ago"
    if hours >= 1:
        return f"{int(hours)} hours ago"
    if minutes >= 1:
        return f"{int(minutes)} mins ago"
    return "Just now"


# =====================================================
# GET /scripts — Dashboard Script List (LOCKED UI)
# =====================================================

@router.get("")
def list_scripts(
    db: Session = Depends(get_db),
    current_user=Depends(role_required("editor")),
):
    """
    Dashboard Script List

    - Admin: sees all scripts
    - Editor: sees only own scripts
    - Viewer: NOT allowed
    """

    query = db.query(Script)

    # Role-based visibility
    if current_user.role != "admin":
        query = query.filter(Script.created_by == current_user.id)

    scripts = query.order_by(Script.created_at.desc()).all()

    results = []

    for script in scripts:
        # ---------------------------
        # Unified UI Status
        # ---------------------------
        if script.review_status == "approved":
            status = "success"          # completed
        elif script.review_status == "rejected":
            status = "rejected"
        elif script.status == 1:
            status = "running"          # generating
        else:
            status = "draft"            # editable

        # ---------------------------
        # Scene count (safe)
        # ---------------------------
        scene_count = (
            len(script.scene_timings)
            if isinstance(script.scene_timings, list)
            else 0
        )

        # ---------------------------
        # Safe excerpt (NO crashes)
        # ---------------------------
        excerpt_source = (
            script.description
            or script.content
            or script.prompt
            or ""
        )

        results.append({
            "id": script.id,
            "title": script.title or "Untitled Script",
            "excerpt": excerpt_source[:120],
            "status": status,               # StatusBadge-compatible
            "scenes": scene_count,
            "updated": humanize_time(script.created_at),
        })

    return results


# =====================================================
# GET /scripts/{id} — Script Detail (Editor Page)
# =====================================================

@router.get("/{script_id}")
def get_script_detail(
    script_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(role_required("editor")),
):
    """
    Script Detail (Editor Page)

    - Admin: can access any script
    - Editor: only own scripts
    """

    query = db.query(Script).filter(Script.id == script_id)

    # Role-based access
    if current_user.role != "admin":
        query = query.filter(Script.created_by == current_user.id)

    script = query.first()

    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # ---------------------------
    # Unified UI Status
    # ---------------------------
    if script.review_status == "approved":
        status = "success"
    elif script.review_status == "rejected":
        status = "rejected"
    elif script.status == 1:
        status = "running"
    else:
        status = "draft"

    # ---------------------------
    # Scene count
    # ---------------------------
    scene_count = (
        len(script.scene_timings)
        if isinstance(script.scene_timings, list)
        else 0
    )

    # ---------------------------
    # Action Guards (CRITICAL)
    # ---------------------------
    can_edit = (
        status == "draft"
        and script.review_status != "approved"
        and script.publish_ready == 0
    )

    can_analyze = can_edit and bool(script.content)

    can_generate_video = (
        scene_count > 0
        and status == "draft"
        and script.review_status != "rejected"
    )

    # ---------------------------
    # Response (frontend-aligned)
    # ---------------------------
    return {
        "id": script.id,
        "title": script.title or "Untitled Script",
        "content": script.content or "",
        "prompt": script.prompt or "",
        "parsed_json": script.parsed_json,
        "tone": script.tone,
        "language": script.language,
        "length": script.length,
        "status": status,
        "review_status": script.review_status,
        "scene_count": scene_count,
        "word_count": script.word_count,
        "estimated_watch_time_sec": script.estimated_watch_time_sec,
        "scene_timings": script.scene_timings or [],
        "can_edit": can_edit,
        "can_analyze": can_analyze,
        "can_generate_video": can_generate_video,
        "created_at": script.created_at,
        "updated": humanize_time(script.created_at),
    }

@router.post("/{script_id}/analyze")
def analyze_script(
    script_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(role_required("editor")),
):
    """
    Analyze script content and generate scene structure.

    - Admin: can analyze any script
    - Editor: only own scripts
    """

    query = db.query(Script).filter(Script.id == script_id)

    # Role-based access
    if current_user.role != "admin":
        query = query.filter(Script.created_by == current_user.id)

    script = query.first()

    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # ---------------------------
    # Guards
    # ---------------------------
    if script.review_status == "approved":
        raise HTTPException(
            status_code=400,
            detail="Approved scripts cannot be re-analyzed",
        )

    if not script.content or not script.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Script content is empty",
        )

    # Status must be draft
    if script.status != 0:
        raise HTTPException(
            status_code=400,
            detail="Script is not editable",
        )

    # ---------------------------
    # Compute word metrics
    # ---------------------------
    words = script.content.split()
    word_count = len(words)

    # Avg narration speed ≈ 150 wpm → 2.5 words/sec
    estimated_watch_time_sec = math.ceil(word_count / 2.5)

    # ---------------------------
    # Scene generation
    # ---------------------------
    scenes, manifest_path = split_into_scenes(
        script=script,
        voice_length_seconds=estimated_watch_time_sec,
    )

    # ---------------------------
    # Persist results
    # ---------------------------
    script.scene_timings = scenes
    script.word_count = word_count
    script.estimated_watch_time_sec = estimated_watch_time_sec
    script.updated_at = datetime.utcnow()

    db.commit()

    # ---------------------------
    # Response (frontend-ready)
    # ---------------------------
    return {
        "status": "analyzed",
        "script_id": script.id,
        "scene_count": len(scenes),
        "word_count": word_count,
        "estimated_watch_time_sec": estimated_watch_time_sec,
        "scenes": scenes,
    }

# =====================================================
# POST /scripts/generate — AI Script Generation
# =====================================================

@router.post("/generate", response_model=ScriptResponse)
def generate_script_endpoint(
    data: ScriptCreate,
    db: Session = Depends(get_db),
    current_user=Depends(role_required("editor")),
):
    try:
        return create_script(db, data, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# POST /scripts/bulk-generate — Batch AI Generation
# =====================================================

@router.post("/bulk-generate")
def bulk_generate_scripts_endpoint(
    count: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(role_required("editor")),
):
    """
    Generate multiple unique AI scripts

    - Random category per script
    - Validates uniqueness
    - Creates background generation job
    """

    try:
        job = bulk_generate_scripts(
            db=db,
            user_id=current_user.id,
            count=count,
        )

        return {
            "message": f"Successfully generated {job.generated_count}/{job.requested_count} scripts.",
            "job": {
                "id": job.id,
                "status": job.status,
                "requested_count": job.requested_count,
                "generated_count": job.generated_count,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
            },
        }

    except openai.RateLimitError:
        raise HTTPException(429, "OpenAI quota exceeded.")
    except openai.AuthenticationError:
        raise HTTPException(401, "Invalid OpenAI API key.")
    except openai.APIConnectionError:
        raise HTTPException(503, "OpenAI API unavailable.")
    except openai.OpenAIError as e:
        raise HTTPException(500, f"OpenAI error: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {str(e)}")

# =====================================================
# POST /scripts/{id}/generate-video — Manual Dispatch
# =====================================================

@router.post("/{script_id}/generate-video")
def generate_video_for_script(
    script_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(role_required("editor")),
):
    """
    Manually dispatch video generation for an approved script.

    - Admin / Editor only
    - Delegates to VideoOrchestrator
    """

    # -------------------------------------------------
    # 1. Load Script (role-safe)
    # -------------------------------------------------
    query = db.query(Script).filter(Script.id == script_id)

    if current_user.role != "admin":
        query = query.filter(Script.created_by == current_user.id)

    script = query.first()

    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # -------------------------------------------------
    # 2. Guards
    # -------------------------------------------------
    if script.review_status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Script not approved for video generation",
        )

    if not script.scene_timings or not isinstance(script.scene_timings, list):
        raise HTTPException(
            status_code=400,
            detail="Script not analyzed or scenes missing",
        )

    # -------------------------------------------------
    # 3. Prevent duplicate active videos
    # -------------------------------------------------
    active_video = (
        db.query(Video)
        .filter(
            Video.script_id == script.id,
            Video.is_active == 1,
            Video.status.in_(["draft", "rendering", "ready_for_review"]),
        )
        .first()
    )

    if active_video:
        raise HTTPException(
            status_code=409,
            detail="Video generation already in progress for this script",
        )

    # -------------------------------------------------
    # 4. Dispatch via VideoOrchestrator
    # -------------------------------------------------
    orchestrator = VideoOrchestrator(
        db=db,
        script_id=script.id,
        trigger="manual",
        requested_by=current_user.id,
    )

    result = orchestrator.start()

    # -------------------------------------------------
    # 5. Response
    # -------------------------------------------------
    return {
        "status": "queued",
        "dispatch_type": "manual",
        "script_id": script.id,
        **result,
    }
