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

router = APIRouter(prefix="/weak-areas", tags=["Weak Areas"])


@router.post("/", response_model=WeakAreaResponse)
def submit_weak_area(weak_area: WeakAreaCreate, db: Session = Depends(get_db)):
    return create_weak_area(db, weak_area)


@router.get("/user/{user_id}", response_model=list[WeakAreaResponse])
def read_weak_areas_by_user(user_id: int, db: Session = Depends(get_db)):
    return get_weak_areas_by_user(db, user_id)


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