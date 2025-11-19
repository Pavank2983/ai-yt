from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean, text
)
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from app.db.database import Base


class Category(Base):
    __tablename__ = "categories"

    # ---------------------- Core Fields ----------------------
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP")
    )

    # ---------------------- AI-Automation Preferences ----------------------
    prompt_template = Column(Text, nullable=True)
    voice_style = Column(String(100), nullable=True)     # e.g., "narration", "deep", "calm"
    video_style = Column(String(100), nullable=True)     # e.g., "cinematic", "animated", "horror"
    tone = Column(String(50), nullable=True)             # e.g., "dark", "inspirational", "funny"
    thumbnail_theme = Column(String(100), nullable=True) # e.g., "sci-fi neon", "creepy forest"
    script_length = Column(String(20), default="short", server_default=text("'short'"))
    is_active = Column(Boolean, default=True, server_default=text("1"))

    # ---------------------- Relationships ----------------------
    scripts = relationship("Script", back_populates="category", cascade="all, delete")
    creator = relationship("User", back_populates="categories", foreign_keys=[created_by])
    videos = relationship("Video", back_populates="category", cascade="all, delete")
