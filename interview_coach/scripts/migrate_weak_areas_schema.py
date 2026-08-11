"""
Migration: Update user_weak_areas schema
=========================================

Add 5 separate score columns and remove old single avg_score column.

New columns:
- semantic_avg: Conceptual Understanding
- keyword_avg: Technical Vocabulary  
- completeness_avg: Answer Structure
- confidence_avg: Delivery & Confidence
- grammar_avg: Language Clarity

Old columns being removed:
- avg_score: No longer used
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database.connection import engine

def migrate_weak_areas_table():
    """Update weak_areas table schema with 5 separate score columns"""
    
    migrations = [
        # Drop old columns
        "ALTER TABLE user_weak_areas DROP COLUMN IF EXISTS avg_score;",
        
        # Add new columns with defaults
        "ALTER TABLE user_weak_areas ADD COLUMN IF NOT EXISTS semantic_avg FLOAT DEFAULT 0;",
        "ALTER TABLE user_weak_areas ADD COLUMN IF NOT EXISTS keyword_avg FLOAT DEFAULT 0;",
        "ALTER TABLE user_weak_areas ADD COLUMN IF NOT EXISTS completeness_avg FLOAT DEFAULT 0;",
        "ALTER TABLE user_weak_areas ADD COLUMN IF NOT EXISTS confidence_avg FLOAT DEFAULT 0;",
        "ALTER TABLE user_weak_areas ADD COLUMN IF NOT EXISTS grammar_avg FLOAT DEFAULT 0;",
    ]
    
    try:
        with engine.connect() as conn:
            for sql in migrations:
                conn.execute(text(sql))
                print(f"✅ {sql}")
            conn.commit()
        
        print("\n✅ Migration complete: user_weak_areas table updated")
        return True
    
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    print("Starting user_weak_areas table schema migration...\n")
    success = migrate_weak_areas_table()
    sys.exit(0 if success else 1)
