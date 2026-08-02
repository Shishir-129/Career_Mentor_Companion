from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from schemas.response import ResponseCreate, ResponseResponse, ResponseScoreUpdate, HumanFeedbackUpdate
from crud.responses import (
    create_response,
    get_response,
    get_responses_by_session,
    get_responses_by_user,
    update_response_score,
    delete_response
)
from database.connection import get_db
from services.adaptive_scorer import adaptive_scorer

router = APIRouter(prefix="/responses", tags=["Responses"])


@router.post("/", response_model=ResponseResponse)
def submit_response(response: ResponseCreate, db: Session = Depends(get_db)):
    return create_response(db, response)


@router.get("/session/{session_id}", response_model=list[ResponseResponse])
def read_responses_by_session(session_id: int, db: Session = Depends(get_db)):
    return get_responses_by_session(db, session_id)


@router.get("/user/{user_id}", response_model=list[ResponseResponse])
def read_responses_by_user(user_id: int, db: Session = Depends(get_db)):
    return get_responses_by_user(db, user_id)


@router.get("/{response_id}", response_model=ResponseResponse)
def read_response(response_id: int, db: Session = Depends(get_db)):
    response = get_response(db, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    return response


@router.patch("/{response_id}/score", response_model=ResponseResponse)
def score_response(response_id: int, data: ResponseScoreUpdate, db: Session = Depends(get_db)):
    response = update_response_score(db, response_id, data)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    return response


@router.patch("/{response_id}/human-feedback", response_model=ResponseResponse)
def submit_human_feedback(response_id: int, data: HumanFeedbackUpdate, db: Session = Depends(get_db)):
    response = adaptive_scorer.record_human_feedback(db, response_id, data.actual_score)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    return response


@router.delete("/{response_id}", response_model=ResponseResponse)
def remove_response(response_id: int, db: Session = Depends(get_db)):
    response = delete_response(db, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    return response