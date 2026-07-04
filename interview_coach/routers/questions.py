from fastapi import APIRouter, Depends, HTTPException
from schemas.question import QuestionCreate, QuestionResponse
from sqlalchemy.orm import Session
from schemas.question import QuestionCreate, QuestionResponse, SessionRequest
from services.question_generator import get_questions_for_session

from crud.questions import (
    create_question,
    get_questions,
    get_question,
    get_questions_by_role,
    delete_question
)
from database.connection import get_db

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post("/", response_model=QuestionResponse)
def create(question: QuestionCreate, db: Session = Depends(get_db)):
    return create_question(db, question)


@router.get("/", response_model=list[QuestionResponse])
def read_questions(db: Session = Depends(get_db)):
    return get_questions(db)


@router.get("/role/{role}", response_model=list[QuestionResponse])
def read_questions_by_role(role: str, db: Session = Depends(get_db)):
    return get_questions_by_role(db, role)


@router.get("/{question_id}", response_model=QuestionResponse)
def read_question(question_id: int, db: Session = Depends(get_db)):
    question = get_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.delete("/{question_id}", response_model=QuestionResponse)
def remove_question(question_id: int, db: Session = Depends(get_db)):
    question = delete_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.post("/for-session", response_model=list[QuestionResponse])
def questions_for_session(request: SessionRequest, db: Session = Depends(get_db)):
    questions = get_questions_for_session(
        db, request.role, request.level, request.interview_type, request.count
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this profile")
    return questions