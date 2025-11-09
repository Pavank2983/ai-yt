from pydantic import BaseModel
from typing import Optional

class PlatformBase(BaseModel):
    name: str
    description: Optional[str] = None

class PlatformCreate(PlatformBase):
    pass

class PlatformResponse(PlatformBase):
    id: int

    class Config:
        orm_mode = True
