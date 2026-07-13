import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database.connection import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("""
        ALTER TABLE questions
        ADD COLUMN IF NOT EXISTS expected_components TEXT;
    """))
    conn.commit()
    print("Migration complete: 'expected_components' column added to questions table.")
