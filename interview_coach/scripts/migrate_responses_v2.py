import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database.connection import engine
from sqlalchemy import text

MIGRATIONS = [
    # New scoring columns
    "ALTER TABLE responses ADD COLUMN IF NOT EXISTS completeness_score FLOAT;",
    "ALTER TABLE responses ADD COLUMN IF NOT EXISTS answer_quality_score FLOAT;",
    # Feedback storage
    "ALTER TABLE responses ADD COLUMN IF NOT EXISTS strengths TEXT;",
    "ALTER TABLE responses ADD COLUMN IF NOT EXISTS improvements TEXT;",
    # Drop old unused columns
    "ALTER TABLE responses DROP COLUMN IF EXISTS final_score;",
    "ALTER TABLE responses DROP COLUMN IF EXISTS relevance_score;",
]

with engine.connect() as conn:
    for sql in MIGRATIONS:
        conn.execute(text(sql))
        print(f"  OK: {sql[:60]}...")
    conn.commit()

print("\nMigration complete.")
