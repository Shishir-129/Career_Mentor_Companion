"""
Migration: Add alternative answer metadata columns
====================================================

Add alternative_answer_keywords and alternative_answer_components columns
to the questions table, storing per-alternative keywords/components as JSON,
e.g. {"alternative_0": [...], "alternative_1": [...]}.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from database.connection import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("""
        ALTER TABLE questions
        ADD COLUMN IF NOT EXISTS alternative_answer_keywords JSON;
    """))
    conn.execute(text("""
        ALTER TABLE questions
        ADD COLUMN IF NOT EXISTS alternative_answer_components JSON;
    """))
    conn.commit()
    print("Migration complete: 'alternative_answer_keywords' and 'alternative_answer_components' columns added to questions table.")
