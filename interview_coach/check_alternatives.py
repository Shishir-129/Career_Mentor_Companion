import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.connection import SessionLocal
from database.models import Questions
import json

db = SessionLocal()

print("Checking for alternatives in database...\n")

questions_with_alternatives = 0
questions_with_null_answers = 0

for q in db.query(Questions).limit(100).all():
    if q.answers is None:
        questions_with_null_answers += 1
    else:
        try:
            ans_data = q.answers if isinstance(q.answers, dict) else json.loads(q.answers)
            alts = ans_data.get('alternatives', [])
            if alts and len(alts) > 0:
                questions_with_alternatives += 1
                print(f"Found alternatives in Q{q.id}:")
                print(f"  Count: {len(alts)}")
                for i, alt in enumerate(alts):
                    print(f"  Alternative {i}: {str(alt)[:100]}...")
                print()
        except:
            pass

print(f"\nSummary (first 100 questions):")
print(f"Questions with alternatives: {questions_with_alternatives}")
print(f"Questions with null answers: {questions_with_null_answers}")

if questions_with_alternatives == 0:
    print("\nNO ALTERNATIVES FOUND in your database!")
    print("This is why alternative_answer_keywords and alternative_answer_components are NULL")
    print("\nYou need to:")
    print("1. Add alternatives to the 'answers' column")
    print("2. Run backfill script again")

db.close()
