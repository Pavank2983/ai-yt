from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, BigInteger, DECIMAL, text
)
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from app.db.database import Base

# ---------------------- API USAGE ----------------------
class ApiUsage(Base):
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    tool_name = Column(String(100))
    tokens_used = Column(BigInteger, default=0)
    cost = Column(DECIMAL(10, 4), default=0.0)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP")
    )