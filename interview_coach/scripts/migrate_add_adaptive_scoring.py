import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database.connection import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("""
        ALTER TABLE responses
        ADD COLUMN IF NOT EXISTS predicted_score FLOAT;
    """))
    conn.execute(text("""
        ALTER TABLE responses
        ADD COLUMN IF NOT EXISTS final_human_score FLOAT;
    """))
    conn.commit()
    print("Migration complete: 'predicted_score' and 'final_human_score' added to responses table.")
