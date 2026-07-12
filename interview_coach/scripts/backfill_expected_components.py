import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database.connection import SessionLocal
from database.models import Questions
from services.components_generator import generate_expected_components


def backfill():
    db = SessionLocal()

    questions = db.query(Questions).filter(
        Questions.ideal_answer.isnot(None),
        Questions.ideal_answer != "",
        Questions.expected_components.is_(None),
    ).all()

    print(f"Found {len(questions)} questions to backfill...")

    updated = 0
    for q in questions:
        result = generate_expected_components(q.ideal_answer)
        q.expected_components = result  # may be '[]' for very short answers
        updated += 1
        print(f"  Q{q.id}: {result}")

    db.commit()
    db.close()
    print(f"\nDone. Updated: {updated} questions.")


if __name__ == "__main__":
    backfill()

