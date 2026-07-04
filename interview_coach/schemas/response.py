from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ResponseCreate(BaseModel):
    session_id: int
    user_id: int
    question_id: int
    question_type: Optional[str] = None
    topic: Optional[str] = None
    transcript: Optional[str] = None


class ResponseResponse(BaseModel):
    id: int
    session_id: int
    user_id: int
    question_id: int
    question_type: Optional[str]
    topic: Optional[str]
    transcript: Optional[str]
    semantic_score: Optional[float]
    keyword_score: Optional[float]
    grammar_score: Optional[float]
    relevance_score: Optional[float]
    confidence_score: Optional[float]
    final_score: Optional[float]
    missed_keywords: Optional[str]
    llm_feedback: Optional[str]
    speaking_speed: Optional[float]
    pause_count: Optional[int]
    filler_count: Optional[int]
    audio_file_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ResponseScoreUpdate(BaseModel):
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    grammar_score: Optional[float] = None
    relevance_score: Optional[float] = None
    confidence_score: Optional[float] = None
    final_score: Optional[float] = None
    missed_keywords: Optional[str] = None
    llm_feedback: Optional[str] = None
    speaking_speed: Optional[float] = None
    pause_count: Optional[int] = None
    filler_count: Optional[int] = None
    audio_file_path: Optional[str] = None