from sqlalchemy import Column, Integer, String, Date, Text, Boolean, DateTime, ForeignKey, Float
from .connection import Base
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    target_role = Column(String, nullable=False)
    created_at = Column(DateTime, default=now)


class Questions(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False)
    topic = Column(String(100))
    subtopic = Column(String(100))
    difficulty = Column(String(20))
    question_type = Column(String(30), nullable=False)
    question_text = Column(Text)
    ideal_answer = Column(Text)
    keywords = Column(Text)
    expected_components = Column(Text, nullable=True)  # JSON array e.g. '["definition","example"]'
    code_expected = Column(Boolean, default=False)
    verified = Column(Boolean, default=False)
    times_asked = Column(Integer, default=0)
    created_at = Column(DateTime, default=now)


class Sessions(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50))
    total_score = Column(Float)
    theory_score = Column(Float)
    technical_score = Column(Float)
    total_questions = Column(Integer)
    answered = Column(Integer)
    duration_secs = Column(Integer)
    completed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=now)
    ended_at = Column(DateTime, nullable=True)


class Responses(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    question_type = Column(String(30))
    topic = Column(String(100))
    transcript = Column(Text)
    semantic_score = Column(Float)
    keyword_score = Column(Float)
    completeness_score = Column(Float)
    answer_quality_score = Column(Float)
    grammar_score = Column(Float)
    confidence_score = Column(Float)
    missed_keywords = Column(Text)
    llm_feedback = Column(Text)          # FLAN-T5 narrative paragraph
    strengths = Column(Text)             # JSON array  e.g. '["Good vocabulary", ...]'
    improvements = Column(Text)          # JSON array  e.g. '["Add examples", ...]'
    speaking_speed = Column(Float)
    pause_count = Column(Integer)
    filler_count = Column(Integer)
    audio_file_path = Column(String)
    created_at = Column(DateTime, default=now)


class UserWeakAreas(Base):
    __tablename__ = "user_weak_areas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(100))
    topic = Column(String(100))
    question_type = Column(String(30))
    avg_score = Column(Float)
    attempt_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=now)


class UserQuestionHistory(Base):
    __tablename__ = "user_question_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    times_seen = Column(Integer, default=0)
    last_seen = Column(DateTime, default=now)