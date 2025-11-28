from sqlalchemy import (
    Column, Integer, String, Enum, DateTime, ForeignKey, Index, text
)
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from app.db.database import Base


class ScriptGenerationJob(Base):
    __tablename__ = "script_generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    requested_count = Column(Integer, nullable=False)
    generated_count = Column(Integer, default=0)

    status = Column(
        Enum("pending", "running", "completed", "failed", name="job_status_enum"),
        default="pending",
        index=True  # ✅ add index directly on column
    )

    error_message = Column(String(255), nullable=True)
    started_at = Column(
        DateTime(timezone=True),
        index=True,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP")
    )
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationship with User
    creator = relationship("User", back_populates="generation_jobs")

    # ✅ Additional indexes (optional but useful)
    __table_args__ = (
        Index("idx_job_status", "status"),
        Index("idx_job_created_by", "created_by"),
        Index("idx_job_started_at", "started_at"),
    )
