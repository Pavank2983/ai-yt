from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, text
)
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from app.db.database import Base

# ---------------------- WEBHOOKS ----------------------
class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id", ondelete="CASCADE"))
    event_type = Column(String(100))
    payload = Column(JSON)
    processed = Column(Boolean, default=False)
    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP")
    )

    platform = relationship("Platform", back_populates="webhooks")
