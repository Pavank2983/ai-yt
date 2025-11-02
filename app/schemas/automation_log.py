from pydantic import BaseModel
from typing import Optional

class AutomationLogBase(BaseModel):
    name: str
    description: Optional[str] = None

class AutomationLogCreate(AutomationLogBase):
    pass

class AutomationLogResponse(AutomationLogBase):
    id: int

    class Config:
        orm_mode = True
