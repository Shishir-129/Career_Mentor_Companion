import json
import os
import random
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database.models import Questions

load_dotenv()


def get_questions_for_session(
    db: Session, role: str, level: str, interview_type: str, count: int = 5
) -> list:

    # ✅ Normalize inputs — DB stores "Theoretical", frontend might send "technical"
    level = level.lower().strip()
    interview_type = interview_type.strip()

    # Filter 1: role + experience_level + question_type (best match)
    candidates = (
        db.query(Questions)
        .filter(
            Questions.role == role,
            Questions.experience_level == level,
            Questions.question_text.isnot(None),
            Questions.question_type.ilike(f"%{interview_type}%"),
        )
        .limit(60)
        .all()
    )

    # Fallback 1: drop question_type filter
    if not candidates:
        candidates = (
            db.query(Questions)
            .filter(
                Questions.role == role,
                Questions.experience_level == level,
                Questions.question_text.isnot(None),
            )
            .limit(60)
            .all()
        )

    # Fallback 2: drop experience_level filter too
    if not candidates:
        candidates = (
            db.query(Questions)
            .filter(
                Questions.role == role,
                Questions.question_text.isnot(None),
            )
            .limit(60)
            .all()
        )

    if not candidates:
        return []

    if len(candidates) <= count:
        return candidates

    # ✅ Random sample — no Gemini needed
    return random.sample(candidates, count)