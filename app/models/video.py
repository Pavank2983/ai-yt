from sqlalchemy import (
    Column, Integer, String, Text, Enum, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# ---------------------- VIDEOS ----------------------
class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"))
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"))
    platform_id = Column(Integer, ForeignKey("platforms.id", ondelete="CASCADE"))
    title = Column(String(255))
    description = Column(Text)
    file_url = Column(Text)
    thumbnail_url = Column(Text)
    status = Column(Enum("draft", "rendering", "uploaded", "failed", name="video_status"))
    upload_response = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    uploaded_at = Column(DateTime)

    script = relationship("Script", back_populates="videos")
    category = relationship("Category", back_populates="videos")
    platform = relationship("Platform", back_populates="videos")
    issues = relationship("VideoIssue", back_populates="video", cascade="all, delete")
    logs = relationship("AutomationLog", back_populates="video", cascade="all, delete")
    analytics = relationship("Analytic", back_populates="video", cascade="all, delete")
