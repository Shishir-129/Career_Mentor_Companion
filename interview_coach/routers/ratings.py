from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas.rating import RatingCreate, RatingResponse
from crud.ratings import create_or_update_rating
from database.connection import get_db

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.post("/", response_model=RatingResponse)
def submit_rating(rating: RatingCreate, db: Session = Depends(get_db)):
    return create_or_update_rating(db, rating)
