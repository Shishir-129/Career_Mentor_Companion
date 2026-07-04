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


def delete_weak_area(db: Session, weak_area_id: int):
    weak_area = get_weak_area(db, weak_area_id)
    if not weak_area:
        return None
    db.delete(weak_area)
    db.commit()
    return weak_area