from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class QuestionCreate(BaseModel):
    role: str
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    difficulty: Optional[str] = None
    experience_level: Optional[str] = None   # ✅ new
    question_type: str
    question_text: Optional[str] = None
    ideal_answer: Optional[str] = None
    keywords: Optional[str] = None
    expected_components: Optional[str] = None
    code_expected: bool = False
    verified: bool = False


class QuestionResponse(BaseModel):
    id: int
    role: str
    topic: Optional[str]
    subtopic: Optional[str]
    difficulty: Optional[str]
    experience_level: Optional[str]          # ✅ new
    question_type: str
    question_text: Optional[str]
    ideal_answer: Optional[str]
    keywords: Optional[str]
    expected_components: Optional[str]
    code_expected: bool
    verified: bool
    times_asked: int
    created_at: datetime

    class Config:
        from_attributes = True

        
class SessionRequest(BaseModel):
    role: str           # "Data Analyst" | "Data Scientist" | ...
    level: str          # "fresher" | "junior" | "mid-level" | "senior"
    interview_type: str # "Technical" | "Behavioral" | "Theoretical" | "Mixed"
    difficulty: str = "Medium"  # "Easy" | "Medium" | "Hard"
    count: int = 5