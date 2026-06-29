from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    target_role = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    sessions = relationship("Sessions", back_populates="user", cascade="all, delete-orphan")
    responses = relationship("Responses", back_populates="user", cascade="all, delete-orphan")
    weak_areas = relationship("UserWeakAreas", back_populates="user", cascade="all, delete-orphan")
    question_history = relationship("UserQuestionHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.target_role}>"


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
    code_expected = Column(Boolean, default=False)
    verified = Column(Boolean, default=False)
    times_asked = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    responses = relationship("Responses", back_populates="question")
    history = relationship("UserQuestionHistory", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Questions id={self.id} role={self.role} topic={self.topic} type={self.question_type}>"


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
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
    responses = relationship("Responses", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Sessions id={self.id} user_id={self.user_id} completed={self.completed} score={self.total_score}>"


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
    grammar_score = Column(Float)
    relevance_score = Column(Float)
    confidence_score = Column(Float)
    final_score = Column(Float)
    missed_keywords = Column(Text)
    llm_feedback = Column(Text)
    speaking_speed = Column(Float)
    pause_count = Column(Integer)
    filler_count = Column(Integer)
    audio_file_path = Column(String(255))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    session = relationship("Sessions", back_populates="responses")
    user = relationship("User", back_populates="responses")
    question = relationship("Questions", back_populates="responses")

    def __repr__(self):
        return f"<Responses id={self.id} session_id={self.session_id} user_id={self.user_id} final_score={self.final_score}>"


class UserWeakAreas(Base):
    __tablename__ = "user_weak_areas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(100))
    topic = Column(String(100))
    question_type = Column(String(30))
    avg_score = Column(Float)
    attempt_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="weak_areas")

    def __repr__(self):
        return f"<UserWeakAreas id={self.id} user_id={self.user_id} topic={self.topic} avg_score={self.avg_score}>"


class UserQuestionHistory(Base):
    __tablename__ = "user_question_history"

    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_user_question"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    times_seen = Column(Integer, default=0)
    last_seen = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="question_history")
    question = relationship("Questions", back_populates="history")

    def __repr__(self):
        return f"<UserQuestionHistory id={self.id} user_id={self.user_id} question_id={self.question_id} times_seen={self.times_seen}>"