from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class ScriptCreate(BaseModel):
    prompt: str
    category_id: Optional[int] = None
    tone: Optional[str] = "neutral"
    length: Optional[str] = "short"  # short | medium | long
    language: Optional[str] = "English"
    temperature: Optional[float] = 0.8
    model_used: Optional[str] = "gpt-4o-mini"


class ScriptResponse(BaseModel):
    id: int
    title: Optional[str]
    content: str
    parsed_json: Optional[Any]
    category_id: Optional[int]
    tone: Optional[str]
    length: Optional[str]
    language: Optional[str]
    model_used: Optional[str]
    ai_generated: bool
    status: int
    created_at: datetime

    class Config:
        from_attributes = True
