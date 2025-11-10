from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # AI-Automation specific preferences
    prompt_template = Column(Text, nullable=True)
    voice_style = Column(String(100), nullable=True)
    video_style = Column(String(100), nullable=True)
    tone = Column(String(50), nullable=True)
    thumbnail_theme = Column(String(100), nullable=True)
    script_length = Column(String(20), default="short")  # ✅ NEW COLUMN
    is_active = Column(Boolean, default=True)

    # Relationships
    scripts = relationship("Script", back_populates="category", cascade="all, delete")
    creator = relationship("User", back_populates="categories", foreign_keys=[created_by])
    videos = relationship("Video", back_populates="category", cascade="all, delete")