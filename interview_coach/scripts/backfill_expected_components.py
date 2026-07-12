import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database.connection import SessionLocal
from database.models import Questions
from services.components_generator import generate_expected_components


def backfill():
    db = SessionLocal()

    # Load only the columns we need as plain tuples — avoids ORM expiry issues
    # after commit and keeps memory usage low
    rows = (
        db.query(Questions.id, Questions.ideal_answer)
        .filter(
            Questions.ideal_answer.isnot(None),
            Questions.ideal_answer != "",
            Questions.expected_components.is_(None),
        )
        .all()
    )

    print(f"Found {len(rows)} questions to backfill...")

    updated = 0
    updates = {}   # {id: result} — collected before any DB write

    for q_id, ideal_answer in rows:
        result = generate_expected_components(ideal_answer)
        updates[q_id] = result
        print(f"  Q{q_id}: {result}")
        updated += 1

    # Single bulk update + single commit — connection stays alive
    for q_id, result in updates.items():
        db.query(Questions).filter(Questions.id == q_id).update(
            {"expected_components": result}
        )

    db.commit()
    db.close()
    print(f"\nDone. Updated: {updated} questions.")


if __name__ == "__main__":
    backfill()


