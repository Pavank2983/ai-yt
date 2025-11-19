from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Voice(Base):
    __tablename__ = "voices"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)

    # ---------------------- Voice Info ----------------------
    provider = Column(String(50), nullable=False)              # e.g. "OpenAI", "ElevenLabs", "Google"
    voice_name = Column(String(100), nullable=True)            # e.g. "Alloy", "Rachel", etc.
    style = Column(String(50), nullable=True)                  # e.g. "narration", "news", "horror"
    language = Column(String(50), default="English", server_default=text("'English'"))

    # ---------------------- File Info ----------------------
    file_path = Column(String(255), nullable=False)            # Path to generated audio file
    file_size = Column(Float, nullable=True)                   # File size (MB)
    duration = Column(Float, default=0.0, server_default=text("0.0"))  # Duration in seconds
    audio_format = Column(String(10), default="mp3", server_default=text("'mp3'"))

    # ---------------------- Metadata ----------------------
    settings = Column(JSON, nullable=True)                     # JSON: pitch, stability, similarity, etc.
    is_primary = Column(Boolean, default=False, server_default=text("0"))  # main voice flag
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ---------------------- Relationships ----------------------
    script = relationship("Script", back_populates="voices")
