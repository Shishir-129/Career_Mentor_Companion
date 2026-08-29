from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from schemas.weak_area import WeakAreaCreate, WeakAreaResponse, WeakAreaScoreUpdate
from crud.weak_areas import (
    create_weak_area,
    get_weak_area,
    get_weak_areas_by_user,
    update_weak_area_score,
    delete_weak_area
)
from database.connection import get_db
from database.models import Responses

router = APIRouter(prefix="/weak-areas", tags=["Weak Areas"])


def _enrich_weak_area_with_question_types(db: Session, weak_area):
    """Add question_types and is_behavioral_only to weak area response"""
    responses = db.query(Responses).filter(
        Responses.topic == weak_area.topic,
        Responses.user_id == weak_area.user_id
    ).all()
    
    question_types = list(set([r.question_type for r in responses if r.question_type]))
    is_behavioral_only = len(question_types) == 1 and question_types[0] == "behavioral"
    
    # Convert to dict and add fields
    result = weak_area.__dict__.copy()
    result['question_types'] = question_types
    result['is_behavioral_only'] = is_behavioral_only
    return result


@router.post("/", response_model=WeakAreaResponse)
def submit_weak_area(weak_area: WeakAreaCreate, db: Session = Depends(get_db)):
    return create_weak_area(db, weak_area)


@router.get("/user/{user_id}", response_model=list[WeakAreaResponse])
def read_weak_areas_by_user(user_id: int, db: Session = Depends(get_db)):
    weak_areas = get_weak_areas_by_user(db, user_id)
    return [_enrich_weak_area_with_question_types(db, wa) for wa in weak_areas]


@router.get("/{weak_area_id}", response_model=WeakAreaResponse)
def read_weak_area(weak_area_id: int, db: Session = Depends(get_db)):
    weak_area = get_weak_area(db, weak_area_id)
    if not weak_area:
        raise HTTPException(status_code=404, detail="Weak area not found")
    return weak_area


@router.patch("/{weak_area_id}/score", response_model=WeakAreaResponse)
def score_weak_area(weak_area_id: int, data: WeakAreaScoreUpdate, db: Session = Depends(get_db)):
    weak_area = update_weak_area_score(db, weak_area_id, data)
    if not weak_area:
        raise HTTPException(status_code=404, detail="Weak area not found")
    return weak_area


@router.delete("/{weak_area_id}", response_model=WeakAreaResponse)
def remove_weak_area(weak_area_id: int, db: Session = Depends(get_db)):
    weak_area = delete_weak_area(db, weak_area_id)
    if not weak_area:
        raise HTTPException(status_code=404, detail="Weak area not found")
    return weak_area