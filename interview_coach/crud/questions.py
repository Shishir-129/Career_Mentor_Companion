from sqlalchemy.orm import Session
from database.models import Questions
from schemas.question import QuestionCreate, QuestionResponse

from typing import Optional
from datetime import datetime

def create_question(db: Session, question: QuestionCreate):
    db_question = Questions(**question.model_dump())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def get_questions(db: Session):
    return db.query(Questions).all()

def get_question(db: Session, question_id: int):
    return db.query(Questions).filter(Questions.id == question_id).first()

def get_questions_by_role(db: Session, role: str):
    return db.query(Questions).filter(Questions.role == role).all()

def delete_question(db: Session, question_id: int):
    question = get_question(db, question_id)
    if not question:
        return None
    db.delete(question)
    db.commit()
    return question