import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database.connection import SessionLocal
from services.adaptive_scorer import adaptive_scorer

db = SessionLocal()
try:
    result = adaptive_scorer.retrain_from_db(db)
    print(result)
finally:
    db.close()
