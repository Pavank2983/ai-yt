from sqlalchemy import (
    Column, Integer, String, Enum, DateTime
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# ---------------------- USERS ----------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))
    role = Column(Enum("admin", "editor", "viewer", name="user_roles"))
    status = Column(Enum("active", "inactive", name="user_status"), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    categories = relationship("Category", back_populates="creator", cascade="all, delete")
    scripts = relationship("Script", back_populates="creator", cascade="all, delete")
    platforms = relationship("Platform", back_populates="owner", cascade="all, delete")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete")