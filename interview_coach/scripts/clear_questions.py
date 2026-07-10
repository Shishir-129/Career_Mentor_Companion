import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database.connection import SessionLocal
from database.models import Questions

db = SessionLocal()
deleted = db.query(Questions).delete()
db.commit()
db.close()
print(f"Deleted {deleted} questions from DB.")
