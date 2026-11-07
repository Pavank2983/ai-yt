from sqlalchemy import (
    Boolean, Column, Integer, String, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.db.database import Base

# ---------------------- PLATFORMS ------------------------
class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    access_token = Column(Text)
    refresh_token = Column(Text)
    expires_at = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    owner = relationship("User", back_populates="platforms")
    videos = relationship("Video", back_populates="platform", cascade="all, delete")
    webhooks = relationship("Webhook", back_populates="platform", cascade="all, delete")