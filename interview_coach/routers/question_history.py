from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from schemas.question_history import (
    QuestionHistoryCreate,
    QuestionHistoryUpdate,
    QuestionHistoryResponse
)
from crud.question_history import (
    create_question_history,
    get_question_history,
    get_history_by_user,
    increment_question_seen,
    update_question_history,
    delete_question_history
)
from database.connection import get_db

router = APIRouter(prefix="/question-history", tags=["Question History"])


@router.post("/", response_model=QuestionHistoryResponse)
def submit_question_history(history: QuestionHistoryCreate, db: Session = Depends(get_db)):
    return create_question_history(db, history)


@router.post("/seen", response_model=QuestionHistoryResponse)
def mark_question_seen(user_id: int, question_id: int, db: Session = Depends(get_db)):
    return increment_question_seen(db, user_id, question_id)


@router.get("/user/{user_id}", response_model=list[QuestionHistoryResponse])
def read_history_by_user(user_id: int, db: Session = Depends(get_db)):
    return get_history_by_user(db, user_id)


@router.get("/{history_id}", response_model=QuestionHistoryResponse)
def read_question_history(history_id: int, db: Session = Depends(get_db)):
    history = get_question_history(db, history_id)
    if not history:
        raise HTTPException(status_code=404, detail="Question history not found")
    return history


@router.patch("/{history_id}", response_model=QuestionHistoryResponse)
def edit_question_history(history_id: int, data: QuestionHistoryUpdate, db: Session = Depends(get_db)):
    history = update_question_history(db, history_id, data)
    if not history:
        raise HTTPException(status_code=404, detail="Question history not found")
    return history


@router.delete("/{history_id}", response_model=QuestionHistoryResponse)
def remove_question_history(history_id: int, db: Session = Depends(get_db)):
    history = delete_question_history(db, history_id)
    if not history:
        raise HTTPException(status_code=404, detail="Question history not found")
    return history