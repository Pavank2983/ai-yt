import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


# ---------------------------------------------------------
# ENUM: Platform Upload Status
# ---------------------------------------------------------
class PlatformUploadStatus(str, enum.Enum):
    pending = "pending"
    uploading = "uploading"
    success = "success"
    failed = "failed"


# ---------------------------------------------------------
# MODEL
# ---------------------------------------------------------
class VideoPlatformStatus(Base):
    __tablename__ = "video_platform_status"
    __table_args__ = (
        UniqueConstraint(
            "video_id",
            "platform_id",
            name="uq_video_platform_status_video_platform",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    # -----------------------------------------------------
    # RELATIONS
    # -----------------------------------------------------
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)

    video = relationship("Video", backref="platform_statuses")
    platform = relationship("Platform")

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------
    status = Column(
        Enum(PlatformUploadStatus),
        default=PlatformUploadStatus.pending,
        nullable=False
    )

    # -----------------------------------------------------
    # RESULT DATA
    # -----------------------------------------------------
    uploaded_url = Column(String, nullable=True)   # final URL (YouTube, etc.)
    error = Column(Text, nullable=True)

    # -----------------------------------------------------
    # TIMESTAMPS
    # -----------------------------------------------------
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
