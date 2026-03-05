from sqlalchemy import (
    Column, Integer, String, Text, Enum, DateTime,
    ForeignKey, JSON, Float, Boolean, text, DECIMAL
)
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from app.db.database import Base

import enum
class ApprovalStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)

    # --------------------------------------------------
    # Core Relations
    # --------------------------------------------------
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"))
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"))
    platform_id = Column(Integer, ForeignKey("platforms.id", ondelete="CASCADE"))

    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------
    title = Column(String(255))
    description = Column(Text)
    file_url = Column(Text)
    thumbnail_url = Column(Text)
    voice_file_url = Column(Text)

    # --------------------------------------------------
    # AI / Generation Info
    # --------------------------------------------------
    ai_provider = Column(String(50), index=True)
    ai_prompt_used = Column(Text)
    generation_mode = Column(String(20), default="AI", server_default=text("'AI'"))
    resolution = Column(String(20))
    video_length = Column(Float)
    render_time = Column(Float)

    # --------------------------------------------------
    # 💰 Cost Intelligence (NEW)
    # --------------------------------------------------
    estimated_total_cost = Column(DECIMAL(12, 4), nullable=True)
    actual_total_cost = Column(DECIMAL(12, 4), nullable=True)
    cost_breakdown_json = Column(LONGTEXT, nullable=True)

    # --------------------------------------------------
    # Runtime / Errors
    # --------------------------------------------------
    view_count = Column(Integer, server_default=text("0"))
    error_log = Column(LONGTEXT, nullable=True)

    status = Column(
        Enum(
            "draft",
            "rendering",
            "ready_for_review",
            "uploaded",
            "failed",
            name="video_status"
        ),
        server_default=text("'draft'"),
        index=True
    )

    upload_response = Column(JSON)

    # --------------------------------------------------
    # 🔐 APPROVAL WORKFLOW
    # --------------------------------------------------
    approval_status = Column(
        Enum(ApprovalStatus, name="video_approval_status"),
        server_default=text("'pending_review'"),
        index=True
    )

    approved_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    scheduled_at = Column(DateTime, nullable=True)

    # --------------------------------------------------
    # System Fields
    # --------------------------------------------------
    is_active = Column(Boolean, server_default=text("1"), index=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    uploaded_at = Column(DateTime)

    assets_manifest = Column(Text, nullable=True)
    final_duration = Column(Integer, nullable=True)
    final_resolution = Column(String(50), nullable=True)

    # --------------------------------------------------
    # Relationships
    # --------------------------------------------------
    script = relationship("Script", back_populates="videos")
    category = relationship("Category", back_populates="videos")
    platform = relationship("Platform", back_populates="videos")

    issues = relationship("VideoIssue", back_populates="video", cascade="all, delete")
    logs = relationship("AutomationLog", back_populates="video", cascade="all, delete")
    analytics = relationship("Analytic", back_populates="video", cascade="all, delete")
    jobs = relationship("VideoJob", back_populates="video", cascade="all, delete-orphan")
    merge_jobs = relationship("VideoMergeJob", back_populates="video", cascade="all, delete-orphan")
