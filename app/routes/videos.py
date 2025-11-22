import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Script
from app.services.scene_splitter import split_into_scenes
from app.core.security import role_required
from app.services.orchestrator.scene_job_orchestrator import SceneJobOrchestrator

router = APIRouter(prefix="/videos")

VALID_PROVIDERS = {"MINIMAX", "VEO", "SORA", "KLING", "RUNWAY"}


# -------------------------------------------------------------
#  POST /videos/generate/{script_id}
# -------------------------------------------------------------
@router.post("/generate/{script_id}")
def queue_video_generation(
    script_id: int,
    provider: str | None = None,
    voice_length_seconds: float | None = None,
    quality: str = "DEV",
    db: Session = Depends(get_db),
    current_user=Depends(role_required("editor")),
):
    """
    QUEUE AI VIDEO GENERATION PIPELINE

    Steps:
    1. Validate script
    2. Validate provider and determine from env fallback
    3. Determine voice audio duration
    4. Run Scene Splitter
    5. Call Class-based Orchestrator
    """

    # ---------------------------------------------------------
    # 1. Load Script
    # ---------------------------------------------------------
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # ---------------------------------------------------------
    # 2. Provider selection
    # ---------------------------------------------------------
    env_provider = os.getenv("AI_VIDEO_PROVIDER", "MINIMAX").upper()
    selected_provider = (provider or env_provider).upper()

    if selected_provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider '{selected_provider}'. Allowed: {', '.join(VALID_PROVIDERS)}",
        )

    # ---------------------------------------------------------
    # 3. Determine voice duration
    # ---------------------------------------------------------
    voice_length_seconds = (
        voice_length_seconds or getattr(script, "audio_duration_seconds", None)
    )

    if voice_length_seconds is None:
        raise HTTPException(
            status_code=400,
            detail="voice_length_seconds missing — generate TTS first.",
        )

    # ---------------------------------------------------------
    # 4. SCENE SPLITTING
    # ---------------------------------------------------------
    scenes, manifest_path = split_into_scenes(
        script,
        voice_length_seconds,
    )

    if not scenes:
        raise HTTPException(
            status_code=422,
            detail="Scene splitter returned 0 scenes.",
        )

    # ---------------------------------------------------------
    # 5. ORCHESTRATOR: CREATE VIDEO + JOBS + MERGE TASK
    # ---------------------------------------------------------
    orchestrator = SceneJobOrchestrator(
        db=db,
        script_id=script_id,
        scenes=scenes,
        voice_length_seconds=voice_length_seconds,
        provider=selected_provider,
        quality=quality,
    )

    result = orchestrator.run()

    return {
        "message": "Multi-scene AI video generation queued successfully",
        "script_id": script_id,
        "provider": selected_provider,
        **result,
    }


# -------------------------------------------------------------
#  GET /videos/jobs/{job_id}
# -------------------------------------------------------------
@router.get("/jobs/{job_id}")
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """
    Returns: VideoJob status + metadata
    """

    from app.models.video_job import VideoJob

    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "video_id": job.video_id,
        "provider": job.provider,
        "status": job.status.value,
        "task_id": job.task_id,
        "file_id": job.file_id,
        "video_url": job.video_url,
        "local_path": job.local_path,
        "scene_index": job.scene_index,
        "error_log": job.error_log,
        "attempts": job.attempts,
        "meta": job.meta,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "completed_at": job.completed_at,
    }
