from google import genai
import json
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database.models import Questions

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Map experience level → difficulty stored in DB
LEVEL_TO_DIFFICULTY = {
    "fresher": ["easy"],
    "junior": ["easy", "medium"],
    "mid-level": ["medium"],
    "senior": ["medium", "expert"],
}


def get_questions_for_session(
    db: Session, role: str, level: str, interview_type: str, count: int = 5
) -> list:
    difficulties = LEVEL_TO_DIFFICULTY.get(level.lower(), ["medium"])

    # Pre-filter from DB by difficulty (keeps Gemini prompt small)
    candidates = (
        db.query(Questions)
        .filter(
            Questions.difficulty.in_(difficulties), Questions.question_text.isnot(None)
        )
        .limit(60)
        .all()
    )

    if not candidates:
        return []

    pool = [
        {
            "id": q.id,
            "topic": q.topic,
            "question": q.question_text,
            "type": q.question_type,
        }
        for q in candidates
    ]

    prompt = f"""You are an expert interview coach for Data Science roles.

Candidate profile:
- Job Role: {role}
- Experience Level: {level}
- Interview Type: {interview_type}

From the question bank below, select exactly {count} questions most relevant 
to this candidate's role and interview type. Prioritize topic fit for the role.

Question bank:
{json.dumps(pool, indent=2)}

Return ONLY a JSON array of the selected question IDs (integers).
Example: [3, 7, 15, 22, 41]"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    selected_ids = set(json.loads(response.text))
    return [q for q in candidates if q.id in selected_ids]
