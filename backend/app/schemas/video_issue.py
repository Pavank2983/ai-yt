from pydantic import BaseModel
from typing import Optional

class VideoIssueBase(BaseModel):
    name: str
    description: Optional[str] = None

class VideoIssueCreate(VideoIssueBase):
    pass

class VideoIssueResponse(VideoIssueBase):
    id: int

    class Config:
        orm_mode = True
