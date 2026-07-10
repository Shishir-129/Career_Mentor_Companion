import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database.connection import SessionLocal
from database.models import Questions

db = SessionLocal()
total = db.query(Questions).count()

no_keywords = db.query(Questions).filter(
    (Questions.keywords == None) | (Questions.keywords == "")
).count()

# Check if answers contain bullet points or code blocks (signs of new scraper)
has_bullets = db.query(Questions).filter(Questions.ideal_answer.contains("- ")).count()
has_code    = db.query(Questions).filter(Questions.ideal_answer.contains("```")).count()

# Sample: show Q2 (regression types - should have bullet points if updated)
q2 = db.query(Questions).filter(Questions.id == 3).first()
db.close()

print(f"Total questions in DB      : {total}")
print(f"Questions with no keywords : {no_keywords}")
print(f"Answers with bullet points : {has_bullets}")
print(f"Answers with code blocks   : {has_code}")
print()
print("Sample answer (ID=3 - should have regression model bullet points if updated):")
print(q2.ideal_answer[:600] if q2 else "Not found")

