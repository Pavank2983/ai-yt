from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum,
    DateTime,
    ForeignKey,
    Text,
    Index,
    Boolean,
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
    # Indexes (Scheduler + Worker optimized)
    # ---------------------------------------------------
    __table_args__ = (

        # 🔍 Provider polling (task_id IS NOT NULL only)
        # Uniqueness enforced at app level (MySQL-safe)
        Index(
            "idx_video_jobs_provider_task_id",
            "provider",
            "task_id",
        ),

        # 🔍 Scheduler hot paths
        Index("idx_video_jobs_status", "status"),
        Index("idx_video_jobs_is_tts_status", "is_tts", "status"),

        # 🔍 Relationship filters
        Index("idx_video_jobs_script_id", "script_id"),
        Index("idx_video_jobs_video_id", "video_id"),

        # 🔍 Scene orchestration
        Index("idx_video_jobs_scene_index", "scene_index"),

        # 🔍 Ordering / fairness
        Index("idx_video_jobs_created_at", "created_at"),
    )

    # ---------------------------------------------------
    # Columns
    # ---------------------------------------------------

    id = Column(Integer, primary_key=True, index=True)

    script_id = Column(
        Integer,
        ForeignKey("scripts.id", ondelete="CASCADE"),
        nullable=False,
    )

    video_id = Column(
        Integer,
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=True,
    )

    # ---------------------------------------------------
    # Job type
    # ---------------------------------------------------
    is_tts = Column(Boolean, default=False, nullable=False)

    # ---------------------------------------------------
    # Provider-specific fields (ONLY for non-TTS jobs)
    # ---------------------------------------------------
    provider = Column(String(50), nullable=True)  # e.g. MINIMAX, RUNWAY
    task_id = Column(String(255), nullable=True)
    file_id = Column(String(255), nullable=True)

    # ---------------------------------------------------
    # Output
    # ---------------------------------------------------
    video_url = Column(Text, nullable=True)
    local_path = Column(String(512), nullable=True)

    # Scene index (NULL for TTS jobs)
    scene_index = Column(Integer, nullable=True)

    # JSON metadata (voice config, prompts, provider response)
    meta = Column(Text, nullable=True)

    # ---------------------------------------------------
    # State
    # ---------------------------------------------------
    status = Column(
        Enum(JobStatus),
        default=JobStatus.queued,
        nullable=False,
    )

    error_log = Column(Text, nullable=True)
    attempts = Column(Integer, default=0)

    # ---------------------------------------------------
    # Timestamps
    # ---------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ---------------------------------------------------
    # Relationships
    # ---------------------------------------------------
    script = relationship("Script", back_populates="video_jobs")
    video = relationship("Video", back_populates="jobs", lazy="joined")

    # ---------------------------------------------------
    # Debug
    # ---------------------------------------------------
    def __repr__(self):
        job_type = "TTS" if self.is_tts else self.provider
        return (
            f"<VideoJob id={self.id} "
            f"type={job_type} "
            f"script={self.script_id} "
            f"video={self.video_id} "
            f"scene={self.scene_index} "
            f"status={self.status}>"
        )
