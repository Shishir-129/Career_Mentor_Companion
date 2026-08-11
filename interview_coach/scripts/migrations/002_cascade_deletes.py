"""
Migration: Add CASCADE delete to foreign keys
==============================================

Ensures that when a user is deleted, all related data cascades:
- sessions
- responses
- user_weak_areas
- user_question_history

This replaces existing constraints with CASCADE versions.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from database.connection import engine

def migrate_cascade_deletes():
    """Add ON DELETE CASCADE to all user foreign keys"""
    
    migrations = [
        # Fix sessions.user_id
        "ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_user_id_fkey;",
        "ALTER TABLE sessions ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;",
        
        # Fix responses.user_id
        "ALTER TABLE responses DROP CONSTRAINT IF EXISTS responses_user_id_fkey;",
        "ALTER TABLE responses ADD CONSTRAINT responses_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;",
        
        # Fix responses.session_id
        "ALTER TABLE responses DROP CONSTRAINT IF EXISTS responses_session_id_fkey;",
        "ALTER TABLE responses ADD CONSTRAINT responses_session_id_fkey FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE;",
        
        # Fix user_weak_areas.user_id
        "ALTER TABLE user_weak_areas DROP CONSTRAINT IF EXISTS user_weak_areas_user_id_fkey;",
        "ALTER TABLE user_weak_areas ADD CONSTRAINT user_weak_areas_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;",
        
        # Fix user_question_history.user_id
        "ALTER TABLE user_question_history DROP CONSTRAINT IF EXISTS user_question_history_user_id_fkey;",
        "ALTER TABLE user_question_history ADD CONSTRAINT user_question_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;",
    ]
    
    try:
        with engine.connect() as conn:
            for sql in migrations:
                conn.execute(text(sql))
                print(f"✅ {sql}")
            conn.commit()
        
        print("\n✅ Migration complete: CASCADE delete constraints applied")
        return True
    
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    print("Starting CASCADE delete migration...\n")
    success = migrate_cascade_deletes()
    sys.exit(0 if success else 1)
