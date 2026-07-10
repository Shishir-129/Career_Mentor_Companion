import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database.connection import SessionLocal
from database.models import Questions
from services.keyword_extractor import extract_keywords

def backfill():
    db = SessionLocal()

    # fetch ALL questions with ideal_answer
    # not just empty ones — we want to overwrite bad keywords too
    questions = db.query(Questions).filter(
        Questions.ideal_answer.isnot(None),
    ).all()

    print(f"Found {len(questions)} questions to backfill...")

    for q in questions:
        extracted = extract_keywords(q.ideal_answer, top_n=8)
        q.keywords = ", ".join(extracted)
        print(f"  Q{q.id}: {q.keywords}")

    db.commit()
    db.close()
    print("Done.")

if __name__ == "__main__":
    backfill()