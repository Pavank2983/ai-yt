from pydantic import BaseModel
from typing import Optional

class VideoBase(BaseModel):
    name: str
    description: Optional[str] = None

class VideoCreate(VideoBase):
    pass

class VideoResponse(VideoBase):
    id: int

    class Config:
        orm_mode = True
