from sqlalchemy import (
    Column, Integer, String, Enum, DateTime, ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base
import enum


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    success = "success"
    failed = "failed"


class VideoJob(Base):
    __tablename__ = "video_jobs"

    # ---------------------------------------------------
    # Indexes (critical for performance + correctness)
    # ---------------------------------------------------
    __table_args__ = (
        Index("ux_video_jobs_provider_task_id", "provider", "task_id", unique=True),
        Index("idx_video_jobs_status", "status"),
        Index("idx_video_jobs_video_id", "video_id"),
        Index("idx_video_jobs_script_id", "script_id"),
        Index("idx_video_jobs_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Core references
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=True)

    # Provider fields
    provider = Column(String(50), default="MINIMAX")
    task_id = Column(String(255), nullable=True)    # async provider job ID
    file_id = Column(String(255), nullable=True)    # file ID for MiniMax (retrieve)
    video_url = Column(Text, nullable=True)         # remote provider URL
    local_path = Column(String(512), nullable=True) # downloaded video path

    # Job state
    status = Column(Enum(JobStatus), default=JobStatus.queued, nullable=False)
    error_log = Column(Text, nullable=True)

    # Provider metadata (full JSON response as string)
    meta = Column(Text, nullable=True)

    # Poll attempts
    attempts = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    script = relationship("Script", back_populates="video_jobs")
    video = relationship("Video", back_populates="video_job", lazy="joined")
