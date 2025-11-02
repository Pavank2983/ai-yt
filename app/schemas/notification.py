from pydantic import BaseModel
from typing import Optional

class NotificationBase(BaseModel):
    name: str
    description: Optional[str] = None

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: int

    class Config:
        orm_mode = True
