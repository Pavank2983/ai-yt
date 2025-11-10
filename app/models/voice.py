from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Voice(Base):
    __tablename__ = "voices"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"))

    # Voice info
    provider = Column(String(50), nullable=False)
    voice_name = Column(String(100), nullable=True)
    style = Column(String(50), nullable=True)
    language = Column(String(50), default="English")

    # File info
    file_path = Column(String(255), nullable=False)
    file_size = Column(Float, nullable=True)
    duration = Column(Float, default=0.0)
    audio_format = Column(String(10), default="mp3")

    # Metadata
    settings = Column(JSON, nullable=True)  # store pitch, stability, boost, etc.
    is_primary = Column(Boolean, default=False)  # main voice used in video
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    script = relationship("Script", back_populates="voices")
