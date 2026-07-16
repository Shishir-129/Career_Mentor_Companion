from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from statistics import mean

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
from database.models import Sessions, Responses

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def calculate_average(values):
    """Calculate average of a list, filtering out None values"""
    valid_values = [v for v in values if v is not None]
    return round(mean(valid_values), 2) if valid_values else 0


def calculate_overall_score(scores_dict):
    """Overall = Answer Quality (70%) + Confidence (30%).
    answer_quality already aggregates semantic, keyword and completeness,
    so there is no need to include them separately.
    """
    quality    = scores_dict.get('answer_quality_avg', 0) or 0
    confidence = scores_dict.get('confidence_avg', 0) or 0
    return round(quality * 0.70 + confidence * 0.30, 2)


@router.post("/", response_model=SessionResponse)
def start_session(session: SessionCreate, db: Session = Depends(get_db)):
    return create_session(db, session)


@router.get("/user/{user_id}/history")
def get_user_sessions(user_id: int, db: Session = Depends(get_db)):
    """Get all sessions for a user with aggregated scores and overall score"""
    try:
        sessions = db.query(Sessions).filter(Sessions.user_id == user_id).all()
        
        if not sessions:
            return []
        
        result = []
        for session in sessions:
            # Get all responses for this session
            responses = db.query(Responses).filter(
                Responses.session_id == session.id
            ).all()
            
            if not responses:
                continue
            
            # Calculate aggregated scores
            scores = {
                'answer_quality_avg': calculate_average([r.answer_quality_score for r in responses]),
                'semantic_avg': calculate_average([r.semantic_score for r in responses]),
                'keyword_avg': calculate_average([r.keyword_score for r in responses]),
                'completeness_avg': calculate_average([r.completeness_score for r in responses]),
                'confidence_avg': calculate_average([r.confidence_score for r in responses]),
                'grammar_avg': calculate_average([r.grammar_score for r in responses]),
            }
            
            # Calculate overall score
            overall_score = calculate_overall_score(scores)
            
            result.append({
                'session_id': session.id,
                'role': session.role,
                'completed': session.completed,
                'started_at': session.started_at,
                'ended_at': session.ended_at,
                'responses_count': len(responses),
                'overall_score': overall_score,
                'scores': scores
            })
        
        # Sort by started_at descending (newest first)
        result.sort(key=lambda x: x['started_at'], reverse=True)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")


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