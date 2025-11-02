from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# ---------------------- SCRIPTS ----------------------
class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    content = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"))
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    ai_generated = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="scripts")
    creator = relationship("User", back_populates="scripts")
    videos = relationship("Video", back_populates="script", cascade="all, delete")