from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.video_issue import VideoIssueCreate
from app.services.video_issue_service import create_video_issue, get_video_issues

router = APIRouter()

@router.post("/")
def add_video_issue(data: VideoIssueCreate, db: Session = Depends(get_db)):
    return create_video_issue(db, data)

@router.get("/")
def list_video_issues(db: Session = Depends(get_db)):
    return get_video_issues(db)
