from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.video import VideoCreate
from app.services.video_service import create_video, get_videos

router = APIRouter()

@router.post("/")
def add_video(data: VideoCreate, db: Session = Depends(get_db)):
    return create_video(db, data)

@router.get("/")
def list_videos(db: Session = Depends(get_db)):
    return get_videos(db)
