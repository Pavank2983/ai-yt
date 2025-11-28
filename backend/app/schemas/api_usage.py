from pydantic import BaseModel
from typing import Optional

class ApiUsageBase(BaseModel):
    name: str
    description: Optional[str] = None

class ApiUsageCreate(ApiUsageBase):
    pass

class ApiUsageResponse(ApiUsageBase):
    id: int

    class Config:
        orm_mode = True
