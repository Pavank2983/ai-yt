from sqlalchemy import (
    Column, Integer, Text, Enum, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# ---------------------- VIDEO ISSUES ----------------------
class VideoIssue(Base):
    __tablename__ = "video_issues"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"))
    issue_type = Column(Enum("copyright", "strike", "policy_violation", "age_restriction", "monetization", name="issue_types"))
    description = Column(Text)
    detected_by = Column(Enum("platform", "manual", "ai", name="detection_sources"))
    status = Column(Enum("active", "resolved", name="issue_status"))
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    video = relationship("Video", back_populates="issues")