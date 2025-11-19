from sqlalchemy import (
    Column, Integer, String, Enum, DateTime, Boolean, text
)
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from app.db.database import Base

# ---------------------- USERS ----------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)

    # Role defaults to 'viewer' at both ORM and DB level
    role = Column(
        Enum("admin", "editor", "viewer", name="user_roles"),
        default="viewer",
        server_default=text("'viewer'"),
        nullable=False
    )

    # Status defaults to 'active' at both ORM and DB level
    status = Column(
        Enum("active", "inactive", name="user_status"),
        default="active",
        server_default=text("'active'"),
        nullable=False
    )

    # Optional active flag for quick deactivation (without deleting)
    is_active = Column(Boolean, server_default=text("1"))

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    categories = relationship("Category", back_populates="creator", cascade="all, delete")
    scripts = relationship(
        "Script",
        back_populates="creator",
        cascade="all, delete",
        foreign_keys="Script.created_by"
    )
    platforms = relationship("Platform", back_populates="owner", cascade="all, delete")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete")
    generation_jobs = relationship("ScriptGenerationJob", back_populates="creator")
