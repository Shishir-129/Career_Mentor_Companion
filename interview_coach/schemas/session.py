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
    theory_score: Optional[float]
    technical_score: Optional[float]
    total_questions: Optional[int]
    answered: Optional[int]
    duration_secs: Optional[int]
    completed: bool
    started_at: datetime
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


class SessionEnd(BaseModel):
    total_score: Optional[float] = None
    theory_score: Optional[float] = None
    technical_score: Optional[float] = None
    total_questions: Optional[int] = None
    answered: Optional[int] = None
    duration_secs: Optional[int] = None

