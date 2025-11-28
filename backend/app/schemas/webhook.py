from pydantic import BaseModel
from typing import Optional

class WebhookBase(BaseModel):
    name: str
    description: Optional[str] = None

class WebhookCreate(WebhookBase):
    pass

class WebhookResponse(WebhookBase):
    id: int

    class Config:
        orm_mode = True
