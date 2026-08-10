from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SessionCreate(BaseModel):
    user_id: int
    role: str

class SessionResponse(BaseModel):
    id: int
    user_id: int
    role: Optional[str]
    total_score: Optional[float]
    total_questions: int
    answered: int
    completed: bool
    started_at: datetime

    class Config:
        from_attributes = True


class SessionEnd(BaseModel):
    total_score: Optional[float] = None

