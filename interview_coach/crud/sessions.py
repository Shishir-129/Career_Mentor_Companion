from sqlalchemy.orm import Session
from database.models import Sessions
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

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(session, key, value)

    session.ended_at = datetime.now(timezone.utc)
    session.completed = True

    db.commit()
    db.refresh(session)
    return session


def delete_session(db: Session, session_id: int):
    session = get_session(db, session_id)
    if not session:
        return None
    db.delete(session)
    db.commit()
    return session