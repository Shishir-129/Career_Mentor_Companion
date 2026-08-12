from sqlalchemy.orm import Session
from database.models import Sessions, Responses
from schemas.session import SessionCreate, SessionEnd
from datetime import datetime, timezone


def create_session(db: Session, session: SessionCreate):
    db_session = Sessions(**session.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_sessions(db: Session):
    return db.query(Sessions).all()


def get_session(db: Session, session_id: int):
    return db.query(Sessions).filter(Sessions.id == session_id).first()


def get_sessions_by_user(db: Session, user_id: int):
    return db.query(Sessions).filter(Sessions.user_id == user_id).all()


def end_session(db: Session, session_id: int, data: SessionEnd):
    session = get_session(db, session_id)
    if not session:
        return None

    responses = db.query(Responses).filter(Responses.session_id == session_id).all()
    answered_count = len(responses)

    # Update session with data from request
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(session, key, value)

    # Auto-calculate overall_score if not provided
    if session.total_score is None and responses:
        # Overall = Answer Quality (70%) + Confidence (30%)
        quality_scores = [r.answer_quality_score for r in responses if r.answer_quality_score is not None]
        confidence_scores = [r.confidence_score for r in responses if r.confidence_score is not None]
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        session.total_score = round(avg_quality * 0.70 + avg_confidence * 0.30, 2)

    # Track answered questions count
    session.answered = answered_count
    # Mark as completed only if all 5 questions are answered
    session.completed = (answered_count == 5)

    db.commit()
    db.refresh(session)
    
    # ✅ Calculate weak areas after session completes
    if session.completed:
        from services.weak_areas_calculator import calculate_and_update_weak_areas
        calculate_and_update_weak_areas(db, session_id, session.user_id, session.role)
    
    return session


def delete_session(db: Session, session_id: int):
    session = get_session(db, session_id)
    if not session:
        return None
    db.delete(session)
    db.commit()
    return session