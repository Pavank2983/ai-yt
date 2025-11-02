from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# ---------------------- WEBHOOKS ----------------------
class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id", ondelete="CASCADE"))
    event_type = Column(String(100))
    payload = Column(JSON)
    processed = Column(Boolean, default=False)
    received_at = Column(DateTime, default=datetime.utcnow)

    platform = relationship("Platform", back_populates="webhooks")
