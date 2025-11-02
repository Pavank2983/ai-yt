from sqlalchemy import (
    Column, Integer, Enum, DateTime, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# ---------------------- JOBS ----------------------
class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum("daily", "manual", name="job_types"))
    status = Column(Enum("pending", "running", "completed", "failed", name="job_status"))
    job_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    logs = relationship("AutomationLog", back_populates="job", cascade="all, delete")