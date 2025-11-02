from sqlalchemy import (
    Column, Integer, Text, Enum, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# ---------------------- AUTOMATION LOGS ----------------------
class AutomationLog(Base):
    __tablename__ = "automation_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"))
    step = Column(Enum("script", "voiceover", "video", "thumbnail", "upload", "metadata", name="automation_steps"))
    status = Column(Enum("success", "failed", "skipped", name="step_status"))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="logs")
    video = relationship("Video", back_populates="logs")