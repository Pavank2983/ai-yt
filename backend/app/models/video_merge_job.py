from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base
import enum


class MergeStatus(str, enum.Enum):
    pending = "pending"
    merging = "merging"
    success = "success"
    failed = "failed"


class VideoMergeJob(Base):
    __tablename__ = "video_merge_jobs"

    id = Column(Integer, primary_key=True, index=True)

    # references
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=True, index=True)

    # merge metadata
    scene_count = Column(Integer, nullable=True)
    quality = Column(String(20), nullable=True)           # DEV / PROD
    merge_mode = Column(String(50), nullable=True)        # e.g. crossfade, slide, concat

    # status/tracking
    status = Column(Enum(MergeStatus), default=MergeStatus.pending, nullable=False, index=True)
    attempts = Column(Integer, default=0)
    worker_id = Column(String(128), nullable=True)        # optional worker identifier
    final_output_path = Column(String(1024), nullable=True)
    manifest_path = Column(String(1024), nullable=True)
    merge_task_path = Column(String(1024), nullable=True)
    error_log = Column(Text, nullable=True)

    # audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # relationships
    video = relationship("Video", back_populates="merge_jobs", lazy="joined")
    script = relationship("Script", lazy="joined")
