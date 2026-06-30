from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from schemas.session import SessionCreate, SessionResponse, SessionEnd
from crud.sessions import (
    create_session,
    get_sessions,
    get_session,
    get_sessions_by_user,
    end_session,
    delete_session
)
from database.connection import get_db

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/", response_model=SessionResponse)
def start_session(session: SessionCreate, db: Session = Depends(get_db)):
    return create_session(db, session)


@router.get("/", response_model=list[SessionResponse])
def read_sessions(db: Session = Depends(get_db)):
    return get_sessions(db)


@router.get("/user/{user_id}", response_model=list[SessionResponse])
def read_sessions_by_user(user_id: int, db: Session = Depends(get_db)):
    return get_sessions_by_user(db, user_id)


@router.get("/{session_id}", response_model=SessionResponse)
def read_session(session_id: int, db: Session = Depends(get_db)):
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}/end", response_model=SessionResponse)
def finish_session(session_id: int, data: SessionEnd, db: Session = Depends(get_db)):
    session = end_session(db, session_id, data)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}", response_model=SessionResponse)
def remove_session(session_id: int, db: Session = Depends(get_db)):
    session = delete_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session