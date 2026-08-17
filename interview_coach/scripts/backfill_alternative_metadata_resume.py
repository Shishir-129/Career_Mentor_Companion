"""
Script: Resume extracting and storing keywords + components for alternative answers
====================================================================================

This script processes ONLY questions that don't have alternative_answer_keywords
yet, in batches of 100. Use this to resume after interruptions.

Run: py scripts/backfill_alternative_metadata_resume.py
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
    batch_size = 50  # Smaller batches for more frequent commits

    try:
        # Get ONLY questions that don't have keywords yet
        pending = db.query(Questions).filter(
            Questions.alternative_answer_keywords.is_(None)
        ).all()
        
        total_pending = len(pending)
        print(f"Found {total_pending} questions still needing keywords/components.\n")

        if total_pending == 0:
            print("All questions already processed!")
            return

        processed_total = 0
        skipped_total = 0

        # Process in batches of 100
        for batch_num in range(0, total_pending, batch_size):
            batch_end = min(batch_num + batch_size, total_pending)
            print(f"\n=== BATCH {batch_num // batch_size + 1} (questions {batch_num}-{batch_end - 1} of {total_pending}) ===")
            
            batch = pending[batch_num:batch_end]
            print(f"Processing {len(batch)} questions...\n")

            processed = 0
            skipped = 0

            for q in batch:
                # Parse the answers JSON column
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

                print(f"  Q{q.id}: {len(keywords_map)} alternatives processed")
                processed += 1

            db.commit()
            processed_total += processed
            skipped_total += skipped
            print(f"\nBatch {batch_num // batch_size + 1} done. Processed: {processed}, Skipped: {skipped}")

        print(f"\n=== FINAL SUMMARY ===")
        print(f"Total Processed: {processed_total}, Total Skipped: {skipped_total}, Grand Total: {total_pending}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    backfill_alternative_metadata()
