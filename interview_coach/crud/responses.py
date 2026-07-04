from sqlalchemy.orm import Session
from database.models import Responses
from schemas.response import ResponseCreate, ResponseScoreUpdate


def create_response(db: Session, response: ResponseCreate):
    db_response = Responses(**response.model_dump())
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response


def get_response(db: Session, response_id: int):
    return db.query(Responses).filter(Responses.id == response_id).first()


def get_responses_by_session(db: Session, session_id: int):
    return db.query(Responses).filter(Responses.session_id == session_id).all()


def get_responses_by_user(db: Session, user_id: int):
    return db.query(Responses).filter(Responses.user_id == user_id).all()


def update_response_score(db: Session, response_id: int, data: ResponseScoreUpdate):
    response = get_response(db, response_id)
    if not response:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(response, key, value)

    db.commit()
    db.refresh(response)
    return response


def delete_response(db: Session, response_id: int):
    response = get_response(db, response_id)
    if not response:
        return None
    db.delete(response)
    db.commit()
    return response