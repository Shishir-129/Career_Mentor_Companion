"""
Fix Questions.answers JSON structure
- Convert NULL → {"alternatives": []}
- Convert {"ideal": "...", "alternatives": [...]} → {"alternatives": [...]}
- Keeps alternatives-only format
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from database.models import Questions
import json

db = SessionLocal()

try:
    all_questions = db.query(Questions).all()
    total = len(all_questions)
    
    print(f"\n{'='*60}")
    print("🔧 Fixing Questions.answers JSON Structure")
    print(f"{'='*60}\n")
    
    fixed_count = 0
    converted_count = 0
    
    for idx, q in enumerate(all_questions, 1):
        try:
            # Case 1: NULL answers → {"alternatives": []}
            if q.answers is None:
                q.answers = json.dumps({"alternatives": []})
                fixed_count += 1
                print(f"[{idx}/{total}] ✓ Fixed NULL → alternatives-only")
            
            else:
                # Parse existing JSON
                ans = json.loads(q.answers)
                
                # Case 2: Has "ideal" key → remove it, keep only alternatives
                if "ideal" in ans and "alternatives" in ans:
                    # Convert to alternatives-only
                    q.answers = json.dumps({"alternatives": ans["alternatives"]})
                    converted_count += 1
                    print(f"[{idx}/{total}] ✓ Converted (removed ideal key)")
                
                # Case 3: Missing "alternatives" key → add it
                elif "alternatives" not in ans:
                    q.answers = json.dumps({"alternatives": []})
                    fixed_count += 1
                    print(f"[{idx}/{total}] ✓ Fixed (missing alternatives key)")
                
                # Case 4: Only has "alternatives" → good, no change needed
                
        except json.JSONDecodeError as e:
            print(f"[{idx}/{total}] ⚠️  Invalid JSON, resetting to empty: {e}")
            q.answers = json.dumps({"alternatives": []})
            fixed_count += 1
        
        except Exception as e:
            print(f"[{idx}/{total}] ❌ Error: {e}")
    
    # Commit changes
    db.commit()
    
    print(f"\n{'='*60}")
    print(f"✅ Complete!")
    print(f"Total questions processed: {total}")
    print(f"Fixed (NULL/malformed): {fixed_count}")
    print(f"Converted (removed ideal): {converted_count}")
    print(f"Already correct: {total - fixed_count - converted_count}")
    print(f"{'='*60}\n")
    
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()

finally:
    db.close()
