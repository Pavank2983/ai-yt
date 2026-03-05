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
    DECIMAL,
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


# ---------------------------------------------------
# Execution Mode (UPDATED)
# ---------------------------------------------------
class JobMode(str, enum.Enum):
    video_api = "video_api"
    synthetic = "synthetic"
    image_motion = "image_motion"   # ✅ NEW (Hybrid Engine Support)


class VideoJob(Base):
    __tablename__ = "video_jobs"

    # ---------------------------------------------------
    # Indexes (Scheduler + Worker optimized)
    # ---------------------------------------------------
    __table_args__ = (

        # Provider polling
        Index(
            "idx_video_jobs_provider_task_id",
            "provider",
            "task_id",
        ),

        # Scheduler hot paths
        Index("idx_video_jobs_status", "status"),
        Index("idx_video_jobs_is_tts_status", "is_tts", "status"),

        # Relationship filters
        Index("idx_video_jobs_script_id", "script_id"),
        Index("idx_video_jobs_video_id", "video_id"),

        # Scene orchestration
        Index("idx_video_jobs_scene_index", "scene_index"),

        # Ordering
        Index("idx_video_jobs_created_at", "created_at"),

        # ✅ NEW: Mode-based scheduling optimization
        Index("idx_video_jobs_mode", "mode"),
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
    # Provider-specific fields
    # ---------------------------------------------------
    provider = Column(String(50), nullable=True)  # MINIMAX, RUNWAY, SYNTHETIC, etc.
    provider_tier = Column(String(20), nullable=True)  # premium / standard / cheap / free

    mode = Column(
        Enum(JobMode),
        default=JobMode.video_api,
        nullable=False,
    )

    task_id = Column(String(255), nullable=True)
    file_id = Column(String(255), nullable=True)

    # ---------------------------------------------------
    # Output
    # ---------------------------------------------------
    video_url = Column(Text, nullable=True)
    local_path = Column(String(512), nullable=True)

    scene_index = Column(Integer, nullable=True)

    # JSON metadata (prompts, provider response, hybrid info, etc.)
    meta = Column(Text, nullable=True)

    # ---------------------------------------------------
    # Cost Tracking
    # ---------------------------------------------------
    estimated_cost = Column(DECIMAL(10, 4), nullable=True)
    actual_cost = Column(DECIMAL(10, 4), nullable=True)

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
            f"tier={self.provider_tier} "
            f"mode={self.mode} "
            f"script={self.script_id} "
            f"video={self.video_id} "
            f"scene={self.scene_index} "
            f"status={self.status} "
            f"attempts={self.attempts}>"
        )