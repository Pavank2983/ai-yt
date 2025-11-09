from pydantic import BaseModel
from typing import Optional

class ScriptBase(BaseModel):
    name: str
    description: Optional[str] = None

class ScriptCreate(ScriptBase):
    pass

class ScriptResponse(ScriptBase):
    id: int

    class Config:
        orm_mode = True
