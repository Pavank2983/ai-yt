from pydantic import BaseModel
from typing import Optional

class JobBase(BaseModel):
    name: str
    description: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: int

    class Config:
        orm_mode = True
