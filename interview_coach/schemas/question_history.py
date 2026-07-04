from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class QuestionHistoryBase(BaseModel):
    times_seen: Optional[int] = 0


class QuestionHistoryCreate(QuestionHistoryBase):
    user_id: int
    question_id: int


class QuestionHistoryUpdate(BaseModel):
    times_seen: Optional[int] = None


class QuestionHistoryResponse(QuestionHistoryBase):
    id: int
    user_id: int
    question_id: int
    last_seen: datetime

    class Config:
        from_attributes = True