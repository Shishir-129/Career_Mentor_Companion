from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class WeakAreaBase(BaseModel):
    role: Optional[str] = None
    topic: Optional[str] = None
    question_type: Optional[str] = None
    avg_score: Optional[float] = None
    attempt_count: Optional[int] = 0


class WeakAreaCreate(WeakAreaBase):
    user_id: int


class WeakAreaScoreUpdate(BaseModel):
    avg_score: float
    attempt_count: Optional[int] = None


class WeakAreaResponse(WeakAreaBase):
    id: int
    user_id: int
    last_updated: datetime

    class Config:
        from_attributes = True