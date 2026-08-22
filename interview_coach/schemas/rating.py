from pydantic import BaseModel, Field
from datetime import datetime


class RatingCreate(BaseModel):
    session_id: int
    user_id: int
    rating: int = Field(ge=1, le=5)


class RatingResponse(BaseModel):
    id: int
    session_id: int
    user_id: int
    rating: int
    created_at: datetime

    class Config:
        from_attributes = True
