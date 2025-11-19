from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Float, text
)
from sqlalchemy.dialects.mysql import LONGTEXT, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), unique=True, nullable=True)

    # ---------------------- Prompt + Content ----------------------
    prompt = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    content = Column(LONGTEXT, nullable=False)
    parsed_json = Column(JSON, nullable=True)

    # ---------------------- Metadata ----------------------
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"))
    tone = Column(String(50), nullable=True)
    length = Column(Enum("short", "medium", "long", name="script_length"), default="short", server_default=text("'short'"))
    language = Column(String(50), default="English", server_default=text("'English'"))
    temperature = Column(Float, default=0.8, server_default=text("0.8"))
    model_used = Column(String(100), default="gpt-4o-mini", server_default=text("'gpt-4o-mini'"))

    # ---------------------- Audio / TTS ----------------------
    tts_voice = Column(String(100), nullable=True)
    tts_params = Column(JSON, nullable=True)
    tts_audio_files = Column(JSON, nullable=True)  # [{line_id, url, duration, size}]
    audio_duration_seconds = Column(Float, default=0.0, server_default=text("0.0"))

    # ---------------------- Video Info ----------------------
    video_params = Column(JSON, nullable=True)
    video_refs = Column(JSON, nullable=True)
    video_duration_seconds = Column(Float, default=0.0, server_default=text("0.0"))

    # ---------------------- Sync / Timing ----------------------
    scene_timings = Column(JSON, nullable=True)
    tts_offsets = Column(JSON, nullable=True)
    captions_srt = Column(Text, nullable=True)
    captions_files = Column(JSON, nullable=True)

    # ---------------------- Provenance / Cost / Performance ----------------------
    retry_count = Column(Integer, default=0, server_default=text("0"))
    generation_cost = Column(Float, default=0.0, server_default=text("0.0"))
    generation_latency_ms = Column(Integer, default=0, server_default=text("0"))
    confidence_score = Column(Float, nullable=True)
    content_hash = Column(String(128), nullable=True)

    # ---------------------- Moderation & Workflow ----------------------
    ai_generated = Column(Boolean, default=True, server_default=text("1"))
    status = Column(Integer, default=0, server_default=text("0"))  # 0 = not used, 1 = video_generated, etc.
    safety_flag = Column(Integer, default=0, server_default=text("0"))  # 0 ok, 1 review, 2 blocked
    content_rating = Column(String(32), nullable=True)
    review_status = Column(
        Enum("pending", "approved", "rejected", name="review_status"),
        default="pending",
        server_default=text("'pending'")
    )
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # ---------------------- Publishing & Variants ----------------------
    parent_script_id = Column(Integer, ForeignKey("scripts.id"), nullable=True)
    version = Column(Integer, default=1, server_default=text("1"))
    publish_ready = Column(Boolean, default=False, server_default=text("0"))
    scheduled_publish_at = Column(DateTime, nullable=True)
    external_upload_id = Column(String(255), nullable=True)

    # ---------------------- SEO / Analytics ----------------------
    word_count = Column(Integer, default=0, server_default=text("0"))
    estimated_watch_time_sec = Column(Float, default=0.0, server_default=text("0.0"))
    keywords = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)

    # ---------------------- Storage Info ----------------------
    storage_provider = Column(String(50), nullable=True)

    # ---------------------- Ownership & Audit ----------------------
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ---------------------- Relationships ----------------------
    category = relationship("Category", back_populates="scripts")
    creator = relationship("User", back_populates="scripts", foreign_keys=[created_by])
    videos = relationship("Video", back_populates="script", cascade="all, delete")
    voices = relationship("Voice", back_populates="script", cascade="all, delete-orphan")
    video_jobs = relationship("VideoJob", back_populates="script", cascade="all, delete-orphan")