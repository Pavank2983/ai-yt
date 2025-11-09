from sqlalchemy.orm import Session
from app.models.video_issue import VideoIssue
from app.schemas.video_issue import VideoIssueCreate

def create_video_issue(db: Session, data: VideoIssueCreate):
    video_issue = VideoIssue(name=data.name, description=data.description)
    db.add(video_issue)
    db.commit()
    db.refresh(video_issue)
    return video_issue

def get_video_issues(db: Session):
    return db.query(VideoIssue).all()
