"""
Weak Areas Calculator Service
==============================
Calculates and updates weak areas from completed session responses.
Groups responses by topic and averages 5 scoring dimensions.
Tracks cumulative attempt_count per topic.
"""

from sqlalchemy.orm import Session
from database.models import Responses
from crud.weak_areas import update_or_create_weak_area


def calculate_and_update_weak_areas(db: Session, session_id: int, user_id: int, role: str):
    """
    Calculate weak areas from responses after session completes.
    
    Args:
        db: Database session
        session_id: Session ID (just completed)
        user_id: User ID
        role: User's target role (e.g., "Data Analyst")
    
    Flow:
        1. Get all responses for this session
        2. Group responses by topic
        3. For each topic:
           - Average the 5 scoring dimensions
           - Calculate attempt count for this topic in this session
           - Update or create weak_area record (cumulative)
    """
    # Get all responses for this session
    responses = db.query(Responses).filter(
        Responses.session_id == session_id,
        Responses.user_id == user_id
    ).all()
    
    if not responses:
        return
    
    # Group responses by topic
    by_topic = {}
    for resp in responses:
        topic = resp.topic or "General"
        if topic not in by_topic:
            by_topic[topic] = []
        by_topic[topic].append(resp)
    
    # Calculate and store weak areas per topic
    for topic, resps in by_topic.items():
        # Calculate averages from responses for this topic
        semantic_avg = (
            sum(r.semantic_score or 0 for r in resps) / len(resps) if resps else 0
        )
        keyword_avg = (
            sum(r.keyword_score or 0 for r in resps) / len(resps) if resps else 0
        )
        completeness_avg = (
            sum(r.completeness_score or 0 for r in resps) / len(resps) if resps else 0
        )
        confidence_avg = (
            sum(r.confidence_score or 0 for r in resps) / len(resps) if resps else 0
        )
        grammar_avg = (
            sum(r.grammar_score or 0 for r in resps) / len(resps) if resps else 0
        )
        
        # Attempt count for this topic in this session
        attempt_count = len(resps)
        
        # Update or create weak area (cumulative attempt_count)
        update_or_create_weak_area(
            db,
            user_id=user_id,
            role=role,
            topic=topic,
            semantic_avg=semantic_avg,
            keyword_avg=keyword_avg,
            completeness_avg=completeness_avg,
            confidence_avg=confidence_avg,
            grammar_avg=grammar_avg,
            attempt_count=attempt_count,
        )
