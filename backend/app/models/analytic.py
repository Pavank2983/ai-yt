from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey, Float, BigInteger, text
)
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from app.db.database import Base

# ---------------------- ANALYTICS ----------------------
class Analytic(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"))
    platform_id = Column(Integer, ForeignKey("platforms.id", ondelete="CASCADE"))
    views = Column(BigInteger, default=0)
    likes = Column(BigInteger, default=0)
    comments = Column(BigInteger, default=0)
    watch_time = Column(Float, default=0.0)
    ctr = Column(Float, default=0.0)
    last_updated = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP")
    )

    video = relationship("Video", back_populates="analytics")