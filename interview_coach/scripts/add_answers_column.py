"""
Add the 'answers' column to the questions table in PostgreSQL
"""

from sqlalchemy import text
from database.connection import engine

def add_answers_column():
    """Add JSON column for storing alternative answers"""
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='questions' AND column_name='answers'
            """))
            
            if result.fetchone():
                print("✓ Column 'answers' already exists")
                return
            
            # Add the column
            conn.execute(text("ALTER TABLE questions ADD COLUMN answers JSON;"))
            conn.commit()
            print("✓ Column 'answers' added successfully to questions table")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Adding 'answers' column to questions table...\n")
    add_answers_column()
