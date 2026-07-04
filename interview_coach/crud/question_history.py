from sqlalchemy.orm import Session
from datetime import datetime

from database.models import UserQuestionHistory
from schemas.question_history import QuestionHistoryCreate, QuestionHistoryUpdate


def create_question_history(db: Session, history: QuestionHistoryCreate):
    db_history = UserQuestionHistory(**history.model_dump())
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history


def get_question_history(db: Session, history_id: int):
    return db.query(UserQuestionHistory).filter(UserQuestionHistory.id == history_id).first()


def get_history_by_user(db: Session, user_id: int):
    return db.query(UserQuestionHistory).filter(UserQuestionHistory.user_id == user_id).all()


def get_history_by_user_and_question(db: Session, user_id: int, question_id: int):
    return db.query(UserQuestionHistory).filter(
        UserQuestionHistory.user_id == user_id,
        UserQuestionHistory.question_id == question_id
    ).first()


def increment_question_seen(db: Session, user_id: int, question_id: int):
    """
    Call this whenever a user is shown a question again.
    Creates a new history row if one doesn't exist yet, otherwise increments times_seen.
    """
    history = get_history_by_user_and_question(db, user_id, question_id)

    if not history:
        history = UserQuestionHistory(
            user_id=user_id,
            question_id=question_id,
            times_seen=1,
            last_seen=datetime.utcnow()
        )
        db.add(history)
    else:
        history.times_seen += 1
        history.last_seen = datetime.utcnow()

    db.commit()
    db.refresh(history)
    return history


def update_question_history(db: Session, history_id: int, data: QuestionHistoryUpdate):
    history = get_question_history(db, history_id)
    if not history:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(history, key, value)

    history.last_seen = datetime.utcnow()

    db.commit()
    db.refresh(history)
    return history


def delete_question_history(db: Session, history_id: int):
    history = get_question_history(db, history_id)
    if not history:
        return None
    db.delete(history)
    db.commit()
    return history