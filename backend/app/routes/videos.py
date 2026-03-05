import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Script
from app.services.scene_splitter import split_into_scenes
from app.core.security import role_required
from app.services.orchestrator.scene_job_orchestrator import SceneJobOrchestrator

router = APIRouter(prefix="/videos")
