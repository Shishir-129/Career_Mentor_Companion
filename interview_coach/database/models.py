from sqlalchemy import Column, Integer, String, Date, Text, Boolean, DateTime, ForeignKey, Float, JSON
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
    difficulty = Column(String(20))
    experience_level = Column(String(20))
    question_type = Column(String(30), nullable=False)
    question_text = Column(Text)
    ideal_answer = Column(Text)
    answers = Column(JSON, nullable=True)  # JSONB: {"ideal": "answer1", "alternatives": ["answer2", "answer3"]}
    keywords = Column(Text)
    expected_components = Column(Text, nullable=True)  # JSON array e.g. '["definition","example"]'
    code_expected = Column(Boolean, default=False)
    times_asked = Column(Integer, default=0)
    created_at = Column(DateTime, default=now)


class Sessions(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50))
    total_score = Column(Float)
    total_questions = Column(Integer, default=5)  # Always 5
    answered = Column(Integer, default=0)  # Number of answered questions (0-5)
    completed = Column(Boolean, default=False)  # True if answered == total_questions
    started_at = Column(DateTime, default=now)


class Responses(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
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
    llm_feedback = Column(Text)          # Score-derived coaching narrative
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
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(100))                           # User's target role
    topic = Column(String(100))                         # Topic (SQL, Python, ML, etc.)
    
    # ✅ 5 Scoring Dimensions (0-100) - averaged from responses for this topic
    semantic_avg = Column(Float, default=0)             # Conceptual Understanding
    keyword_avg = Column(Float, default=0)              # Technical Vocabulary
    completeness_avg = Column(Float, default=0)         # Answer Structure
    confidence_avg = Column(Float, default=0)           # Delivery & Confidence
    grammar_avg = Column(Float, default=0)              # Language Clarity
    
    # Tracking
    attempt_count = Column(Integer, default=0)          # Cumulative: how many times this topic was seen
    last_updated = Column(DateTime, default=now)        # When scores were last recalculated


class UserQuestionHistory(Base):
    __tablename__ = "user_question_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    times_seen = Column(Integer, default=0)
    last_seen = Column(DateTime, default=now)