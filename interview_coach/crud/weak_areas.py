from sqlalchemy.orm import Session
from datetime import datetime

from database.models import UserWeakAreas
from schemas.weak_area import WeakAreaCreate, WeakAreaScoreUpdate


def create_weak_area(db: Session, weak_area: WeakAreaCreate):
    db_weak_area = UserWeakAreas(**weak_area.model_dump())
    db.add(db_weak_area)
    db.commit()
    db.refresh(db_weak_area)
    return db_weak_area


def get_weak_area(db: Session, weak_area_id: int):
    return db.query(UserWeakAreas).filter(UserWeakAreas.id == weak_area_id).first()


def get_weak_areas_by_user(db: Session, user_id: int):
    return db.query(UserWeakAreas).filter(UserWeakAreas.user_id == user_id).all()


def get_weak_area_by_user_topic(db: Session, user_id: int, topic: str):
    """Get weak area for specific user and topic"""
    return db.query(UserWeakAreas).filter(
        UserWeakAreas.user_id == user_id,
        UserWeakAreas.topic == topic
    ).first()


def update_weak_area_score(db: Session, weak_area_id: int, data: WeakAreaScoreUpdate):
    weak_area = get_weak_area(db, weak_area_id)
    if not weak_area:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(weak_area, key, value)

    weak_area.last_updated = datetime.utcnow()

    db.commit()
    db.refresh(weak_area)
    return weak_area


def update_or_create_weak_area(
    db: Session,
    user_id: int,
    role: str,
    topic: str,
    semantic_avg: float,
    keyword_avg: float,
    completeness_avg: float,
    confidence_avg: float,
    grammar_avg: float,
    attempt_count: int,
):
    """Update or create weak area record - called after session completion"""
    weak_area = get_weak_area_by_user_topic(db, user_id, topic)
    
    if weak_area:
        # Update existing: recalculate averages and increment attempt count
        weak_area.semantic_avg = semantic_avg
        weak_area.keyword_avg = keyword_avg
        weak_area.completeness_avg = completeness_avg
        weak_area.confidence_avg = confidence_avg
        weak_area.grammar_avg = grammar_avg
        weak_area.attempt_count += attempt_count  # Cumulative
        weak_area.last_updated = datetime.utcnow()
    else:
        # Create new weak area record
        weak_area = UserWeakAreas(
            user_id=user_id,
            role=role,
            topic=topic,
            semantic_avg=semantic_avg,
            keyword_avg=keyword_avg,
            completeness_avg=completeness_avg,
            confidence_avg=confidence_avg,
            grammar_avg=grammar_avg,
            attempt_count=attempt_count,
            last_updated=datetime.utcnow(),
        )
        db.add(weak_area)
    
    db.commit()
    db.refresh(weak_area)
    return weak_area


def delete_weak_area(db: Session, weak_area_id: int):
    weak_area = get_weak_area(db, weak_area_id)
    if not weak_area:
        return None
    db.delete(weak_area)
    db.commit()
    return weak_area