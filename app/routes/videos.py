import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.database import get_db
from app.models.script import Script
from app.models.video import Video
from app.models.video_job import VideoJob, JobStatus

router = APIRouter(prefix="/videos")

# Allowed providers for validation
VALID_PROVIDERS = {"MINIMAX", "VEO", "SORA", "KLING", "RUNWAY"}


@router.post("/generate/{script_id}")
def queue_video_generation(script_id: int, provider: str | None = None, db: Session = Depends(get_db)):
    """
    Queues a video generation job.
    Creates a Video (draft) + a VideoJob linked to the Video.
    """

    # Validate script exists
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # Provider resolution
    default_provider = os.getenv("AI_VIDEO_PROVIDER", "MINIMAX").upper()
    selected_provider = (provider or default_provider).upper()

    if selected_provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider '{selected_provider}'. Allowed: {', '.join(VALID_PROVIDERS)}"
        )

    # ---------------------------------------------------------
    # 1️⃣  Create a Video row (status = draft)
    # ---------------------------------------------------------
    video = Video(
        script_id=script_id,
        category_id=getattr(script, "category_id", None),
        platform_id=None,
        title=getattr(script, "title", f"AI Video {script_id}"),
        description=(getattr(script, "content", "") or "")[:1000],
        file_url=None,
        thumbnail_url=None,
        voice_file_url=None,
        ai_provider=selected_provider,
        generation_mode="AI",
        status="draft",
        created_at=datetime.now(timezone.utc)
    )

    db.add(video)
    db.commit()
    db.refresh(video)

    # ---------------------------------------------------------
    # 2️⃣  Create the VideoJob row (linked to video)
    # ---------------------------------------------------------
    job = VideoJob(
        script_id=script_id,
        video_id=video.id,
        provider=selected_provider,
        status=JobStatus.queued,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "message": "Video generation job queued successfully",
        "job_id": job.id,
        "video_id": video.id,
        "provider": selected_provider,
        "status": job.status.value,
    }


@router.get("/jobs/{job_id}")
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """
    Returns job status + linked video info.
    """
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
        "error_log": job.error_log,
        "meta": job.meta,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }
