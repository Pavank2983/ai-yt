import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.db.database import get_db
from app.models import Script
from app.services.scene_splitter import split_into_scenes
from app.core.security import role_required
from app.services.orchestrator.scene_job_orchestrator import SceneJobOrchestrator

router = APIRouter()

@router.get("/video/{filename}")
def serve_video(filename: str):

    video_path = os.path.join(
        "assets",
        "cache",
        "video_edits",
        filename
    )

    if not os.path.exists(video_path):
        return {"error": "file not found"}

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename
    )