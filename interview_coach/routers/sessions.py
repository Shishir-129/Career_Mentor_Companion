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


def calculate_overall_score(scores_dict, interview_type: str = "technical"):
    """
    Calculate overall interview score based on interview type.
    
    For Technical Questions:
        Overall = Answer Quality (70%) + Confidence (30%)
        answer_quality already aggregates semantic, keyword and completeness
    
    For Behavioral Questions:
        Overall = Confidence (70%) + Answer Quality (30%)
        Delivery and storytelling matter more than content precision
    """
    quality    = scores_dict.get('answer_quality_avg', 0) or 0
    confidence = scores_dict.get('confidence_avg', 0) or 0
    
    is_behavioral = interview_type.lower().strip() == "behavioral"
    
    if is_behavioral:
        # Behavioral: confidence-first (70% confidence, 30% answer quality)
        return round(confidence * 0.70 + quality * 0.30, 2)
    else:
        # Technical: quality-first (70% answer quality, 30% confidence)
        return round(quality * 0.70 + confidence * 0.30, 2)


def calculate_session_score(responses):
    """
    Calculate session-level overall score as the average of all answered questions.
    
    For each response, the overall_score is already calculated per-question.
    Session score = average of individual question overall scores.
    
    IMPORTANT: If user re-answers the same question multiple times, only count it ONCE.
    answered_count = count of DISTINCT questions answered (max 5), not total responses.
    
    Args:
        responses: List of Response objects from Responses table
    
    Returns:
        Tuple: (overall_session_score, total_questions, answered_count, interview_type)
    """
    if not responses:
        return 0.0, 5, 0, "technical"
    
    # Determine interview type from responses
    interview_type = responses[0].question_type if responses and responses[0].question_type else "technical"
    
    # Count DISTINCT questions answered (not total responses)
    # If user re-answers Q1 twice and Q2 once, answered_count = 2, not 3
    distinct_questions = set()
    for response in responses:
        distinct_questions.add(response.question_id)
    answered_count = len(distinct_questions)
    
    # Calculate overall score for each response
    # For re-answered questions, use the LATEST response (assumption: responses are ordered by time)
    responses_by_question = {}
    for response in responses:
        responses_by_question[response.question_id] = response  # Latest overwrites earlier
    
    overall_scores = []
    for response in responses_by_question.values():
        quality = response.answer_quality_score or 0
        confidence = response.confidence_score or 0
        
        # Apply the same logic as calculate_overall_score
        is_behavioral = interview_type.lower().strip() == "behavioral"
        if is_behavioral:
            overall = confidence * 0.70 + quality * 0.30
        else:
            overall = quality * 0.70 + confidence * 0.30
        
        overall_scores.append(overall)
    
    # Session score is average of answered questions
    session_score = round(mean(overall_scores), 2) if overall_scores else 0.0
    
    return session_score, 5, answered_count, interview_type


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
            
            # Calculate aggregated scores (for detailed breakdown)
            scores = {
                'answer_quality_avg': calculate_average([r.answer_quality_score for r in responses]),
                'semantic_avg': calculate_average([r.semantic_score for r in responses]),
                'keyword_avg': calculate_average([r.keyword_score for r in responses]),
                'completeness_avg': calculate_average([r.completeness_score for r in responses]),
                'confidence_avg': calculate_average([r.confidence_score for r in responses]),
                'grammar_avg': calculate_average([r.grammar_score for r in responses]),
            }
            
            # Calculate session-level overall score (average of all answered questions)
            overall_session_score, total_q, answered_count, interview_type = calculate_session_score(responses)
            
            # Update session metadata
            is_completed = session.completed or (answered_count >= session.total_questions)

            result.append({
                'session_id': session.id,
                'role': session.role,
                'completed': is_completed,
                'started_at': session.started_at,
                'answered': answered_count,
                'total_questions': total_q,
                'overall_score': overall_session_score,  # Always recalculated from responses
                'interview_type': interview_type,
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