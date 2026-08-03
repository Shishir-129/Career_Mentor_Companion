from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime
import json

class ResponseCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: int
    user_id: int
    question_id: int
    question_type: Optional[str] = None
    topic: Optional[str] = None
    transcript: Optional[str] = None
    audio_file_path: Optional[str] = None
    # Scores — populated server-side, optional so client doesn't need to send them
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    completeness_score: Optional[float] = None
    answer_quality_score: Optional[float] = None
    grammar_score: Optional[float] = None
    confidence_score: Optional[float] = None
    missed_keywords: Optional[str] = None
    llm_feedback: Optional[str] = None
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    speaking_speed: Optional[float] = None
    pause_count: Optional[int] = None
    filler_count: Optional[int] = None


class ResponseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int
    user_id: int
    question_id: int
    question_type: Optional[str]
    topic: Optional[str]
    transcript: Optional[str]
    semantic_score: Optional[float]
    keyword_score: Optional[float]
    completeness_score: Optional[float]
    answer_quality_score: Optional[float]
    grammar_score: Optional[float]
    confidence_score: Optional[float]
    missed_keywords: Optional[str]
    llm_feedback: Optional[str]
    strengths: Optional[list[str]] = None
    improvements: Optional[list[str]] = None
    speaking_speed: Optional[float]
    pause_count: Optional[int]
    filler_count: Optional[int]
    audio_file_path: Optional[str]
    predicted_score: Optional[float] = None
    final_human_score: Optional[float] = None
    created_at: datetime

    @field_validator("strengths", "improvements", mode="before")
    @classmethod
    def parse_json_list(cls, v):
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [v]
            except (json.JSONDecodeError, ValueError):
                return [v]
        return v


class ResponseScoreUpdate(BaseModel):
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    completeness_score: Optional[float] = None
    answer_quality_score: Optional[float] = None
    grammar_score: Optional[float] = None
    confidence_score: Optional[float] = None
    missed_keywords: Optional[str] = None
    llm_feedback: Optional[str] = None
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    speaking_speed: Optional[float] = None
    pause_count: Optional[int] = None
    filler_count: Optional[int] = None
    audio_file_path: Optional[str] = None
    predicted_score: Optional[float] = None
    final_human_score: Optional[float] = None


class HumanFeedbackUpdate(BaseModel):
    # scores are on a 0–100 scale, same as answer_quality_score
    actual_score: float = Field(..., ge=0, le=100)
