"""
Count and display distribution of alternative answers across all questions.
Shows how many questions have 0, 1, 2, 3+ alternatives.
"""

import sys
from pathlib import Path

# Add parent directory to path to allow imports from interview_coach
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from database.models import Questions
import json
from collections import Counter

db = SessionLocal()

try:
    all_questions = db.query(Questions).all()
    
    alt_counts = []
    
    for q in all_questions:
        if q.answers:
            ans = json.loads(q.answers)
            alt_counts.append(len(ans['alternatives']))
        else:
            alt_counts.append(0)
    
    # Count distribution
    distribution = Counter(alt_counts)
    
    print("\n" + "="*60)
    print("📊 Alternative Answer Distribution")
    print("="*60)
    
    for num_alts in sorted(distribution.keys()):
        count = distribution[num_alts]
        percentage = (count / len(all_questions)) * 100
        bar = "█" * (count // 5)
        print(f"{num_alts} alternatives: {count:3d} ({percentage:5.1f}%) {bar}")
    
    print("="*60)
    print(f"Total questions: {len(all_questions)}")
    print(f"Average alternatives per question: {sum(alt_counts) / len(all_questions):.2f}")
    print(f"Max alternatives for a single question: {max(alt_counts)}")
    print(f"Questions with at least 1 alternative: {sum(1 for c in alt_counts if c > 0)}")
    print("="*60)
    
except Exception as e:
    print(f"❌ Error: {e}")

finally:
    db.close()
