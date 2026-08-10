"""
Migration script to clean up Sessions table:
  - Drop unused columns: duration_secs, ended_at
  - These were tracked but never actively used
  - Simplifies schema and reduces storage
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import engine
from sqlalchemy import text

MIGRATIONS = [
    "ALTER TABLE sessions DROP COLUMN IF EXISTS duration_secs;",
    "ALTER TABLE sessions DROP COLUMN IF EXISTS ended_at;",
    "ALTER TABLE sessions DROP COLUMN IF EXISTS theory_score;",
    "ALTER TABLE sessions DROP COLUMN IF EXISTS technical_score;",
]

print("\n" + "="*80)
print("MIGRATION: Clean up Sessions table - remove unused columns")
print("="*80 + "\n")

with engine.connect() as conn:
    for sql in MIGRATIONS:
        try:
            conn.execute(text(sql))
            print(f"✅ OK: {sql}")
        except Exception as e:
            print(f"⚠️  {sql}")
            print(f"   {str(e)}")
    conn.commit()

print("\n" + "="*80)
print("Sessions table cleaned up.")
print("Remaining columns: id, user_id, role, total_score, total_questions, answered, completed, started_at")
print("="*80 + "\n")
