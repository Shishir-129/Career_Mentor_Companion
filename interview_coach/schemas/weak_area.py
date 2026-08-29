from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class WeakAreaBase(BaseModel):
    role: Optional[str] = None
    topic: Optional[str] = None
    semantic_avg: Optional[float] = 0
    keyword_avg: Optional[float] = 0
    completeness_avg: Optional[float] = 0
    confidence_avg: Optional[float] = 0
    grammar_avg: Optional[float] = 0
    attempt_count: Optional[int] = 0


class WeakAreaCreate(WeakAreaBase):
    user_id: int


class WeakAreaScoreUpdate(BaseModel):
    """Update scores for a weak area (triggered by session completion)"""
    semantic_avg: float
    keyword_avg: float
    completeness_avg: float
    confidence_avg: float
    grammar_avg: float
    attempt_count: Optional[int] = None


class WeakAreaResponse(WeakAreaBase):
    id: int
    user_id: int
    last_updated: datetime
    question_types: Optional[list[str]] = None  # e.g. ["behavioral", "technical"]
    is_behavioral_only: Optional[bool] = False  # True if only behavioral questions for this topic

    class Config:
        from_attributes = True