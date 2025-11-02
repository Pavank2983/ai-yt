from pydantic import BaseModel
from typing import Optional

class AnalyticBase(BaseModel):
    name: str
    description: Optional[str] = None

class AnalyticCreate(AnalyticBase):
    pass

class AnalyticResponse(AnalyticBase):
    id: int

    class Config:
        orm_mode = True
