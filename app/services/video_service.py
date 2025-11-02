from sqlalchemy.orm import Session
from app.models.video import Video
from app.schemas.video import VideoCreate

def create_video(db: Session, data: VideoCreate):
    video = Video(name=data.name, description=data.description)
    db.add(video)
    db.commit()
    db.refresh(video)
    return video

def get_videos(db: Session):
    return db.query(Video).all()
