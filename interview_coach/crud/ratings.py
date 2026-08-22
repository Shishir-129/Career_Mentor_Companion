from sqlalchemy.orm import Session
from database.models import SessionRatings
from schemas.rating import RatingCreate


def create_or_update_rating(db: Session, rating: RatingCreate):
    existing = db.query(SessionRatings).filter(
        SessionRatings.session_id == rating.session_id
    ).first()

    if existing:
        existing.rating = rating.rating
        db.commit()
        db.refresh(existing)
        return existing

    db_rating = SessionRatings(**rating.model_dump())
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating
