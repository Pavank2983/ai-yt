from sqlalchemy import (
    Column, Integer, Enum, DateTime, JSON, text
)
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from app.db.database import Base

# ---------------------- JOBS ----------------------
class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum("daily", "manual", name="job_types"))
    status = Column(Enum("pending", "running", "completed", "failed", name="job_status"))
    job_metadata = Column(JSON)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP")
    )
    completed_at = Column(DateTime)

    logs = relationship("AutomationLog", back_populates="job", cascade="all, delete")