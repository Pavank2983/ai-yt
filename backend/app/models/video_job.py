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
    # Indexes (Performance + Scheduler Optimization)
    # ---------------------------------------------------
    __table_args__ = (
        # Provider + task_id must be unique to avoid duplicate polling
        Index("ux_video_jobs_provider_task_id", "provider", "task_id", unique=True),

        # Common filtering patterns
        Index("idx_video_jobs_status", "status"),
        Index("idx_video_jobs_script_id", "script_id"),
        Index("idx_video_jobs_video_id", "video_id"),
        Index("idx_video_jobs_scene_index", "scene_index"),
        Index("idx_video_jobs_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)

    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)

    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=True)

    provider = Column(String(50), default="MINIMAX")

    task_id = Column(String(255), nullable=True)
    file_id = Column(String(255), nullable=True)

    video_url = Column(Text, nullable=True)
    local_path = Column(String(512), nullable=True)

    scene_index = Column(Integer, nullable=True)

    meta = Column(Text, nullable=True)

    status = Column(Enum(JobStatus), default=JobStatus.queued, nullable=False)
    error_log = Column(Text, nullable=True)

    # For retry logic
    attempts = Column(Integer, default=0)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    script = relationship("Script", back_populates="video_jobs")

    video = relationship("Video", back_populates="jobs", lazy="joined")

    def __repr__(self):
        return (
            f"<VideoJob id={self.id} "
            f"script={self.script_id} "
            f"video={self.video_id} "
            f"scene={self.scene_index} "
            f"provider={self.provider} "
            f"status={self.status}>"
        )
