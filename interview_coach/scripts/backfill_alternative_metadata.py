"""
Script: Extract and store keywords + components for all alternative answers
=============================================================================

Reads the `answers` JSON column (which holds {"ideal": ..., "alternatives": [...]})
for every question, extracts keywords and expected components for each
alternative answer, and stores the results as JSON in:
  - alternative_answer_keywords   -> {"alternative_0": [...], "alternative_1": [...]}
  - alternative_answer_components -> {"alternative_0": [...], "alternative_1": [...]}

Run: py scripts/backfill_alternative_metadata.py
"""

import sys, os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database.connection import SessionLocal
from database.models import Questions
from services.keyword_extractor import extract_keywords
from services.components_generator import generate_expected_components


def backfill_alternative_metadata():
    db = SessionLocal()
    batch_size = 100

    try:
        # Get total count
        total_count = db.query(Questions).count()
        print(f"Found {total_count} questions total.\n")

        processed_total = 0
        skipped_total = 0

        # Process in batches of 100
        for batch_num in range(0, total_count, batch_size):
            print(f"\n=== BATCH {batch_num // batch_size + 1} (questions {batch_num}-{min(batch_num + batch_size - 1, total_count - 1)}) ===")
            
            questions = db.query(Questions).offset(batch_num).limit(batch_size).all()
            print(f"Processing {len(questions)} questions...\n")

            processed = 0
            skipped = 0

            for q in questions:
                # Parse the answers JSON column (may already be dict or a JSON string)
                answers_data = q.answers
                if isinstance(answers_data, str):
                    try:
                        answers_data = json.loads(answers_data)
                    except (ValueError, TypeError):
                        answers_data = None

                alternatives = []
                if isinstance(answers_data, dict):
                    alternatives = [
                        a for a in answers_data.get("alternatives", [])
                        if a and str(a).strip()
                    ]

                if not alternatives:
                    skipped += 1
                    q.alternative_answer_keywords = None
                    q.alternative_answer_components = None
                    continue

                keywords_map = {}
                components_map = {}

                for idx, alt_text in enumerate(alternatives):
                    alt_key = f"alternative_{idx}"

                    extracted_keywords = extract_keywords(alt_text, top_n=8)
                    keywords_map[alt_key] = extracted_keywords

                    components_json = generate_expected_components(alt_text)
                    components_list = json.loads(components_json) if components_json else []
                    components_map[alt_key] = components_list

                q.alternative_answer_keywords = keywords_map
                q.alternative_answer_components = components_map

                print(f"  Q{q.id}: keywords={keywords_map} components={components_map}")
                processed += 1

            db.commit()
            processed_total += processed
            skipped_total += skipped
            print(f"\nBatch {batch_num // batch_size + 1} done. Processed: {processed}, Skipped: {skipped}")

        print(f"\n=== FINAL SUMMARY ===")
        print(f"Total Processed: {processed_total}, Total Skipped: {skipped_total}, Grand Total: {total_count}")

    finally:
        db.close()


if __name__ == "__main__":
    backfill_alternative_metadata()
