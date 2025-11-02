from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# ---------------------- CATEGORIES ----------------------
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="categories")
    scripts = relationship("Script", back_populates="category", cascade="all, delete")
    videos = relationship("Video", back_populates="category", cascade="all, delete")