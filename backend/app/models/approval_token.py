from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum,
    text,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base
import enum


class ApprovalAction(str, enum.Enum):
    approve = "approve"
    reject = "reject"


class ApprovalToken(Base):
    __tablename__ = "approval_tokens"

    id = Column(Integer, primary_key=True, index=True)

    video_id = Column(
        Integer,
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    token = Column(String(255), unique=True, nullable=False, index=True)

    action = Column(
        Enum(ApprovalAction),
        nullable=False
    )

    expires_at = Column(DateTime(timezone=True), nullable=False)

    used_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP")
    )

    # relationship
    video = relationship("Video")