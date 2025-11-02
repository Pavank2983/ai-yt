from sqlalchemy import (
    Column, Integer, Text, Boolean, Enum, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# ---------------------- NOTIFICATIONS ----------------------
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    message = Column(Text)
    type = Column(Enum("info", "success", "warning", "error", name="notif_types"))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")