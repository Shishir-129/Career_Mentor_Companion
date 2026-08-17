"""
Script: Complete alternative metadata backfill with parallel processing
=========================================================================

Uses ThreadPoolExecutor to extract keywords/components for multiple
questions simultaneously. Only processes questions still missing data.

Run: py scripts/backfill_alternative_metadata_safe.py
"""

import sys, os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database.connection import SessionLocal
from database.models import Questions
from services.keyword_extractor import extract_keywords
from services.components_generator import generate_expected_components


# Thread-safe counter + lock for progress printing
print_lock = Lock()


def process_one_question(q_id: int, answers_raw) -> dict | None:
    """
    Extract keywords + components for all alternatives of ONE question.
    Runs in a worker thread — no DB access here, pure computation only.
    Returns a dict with q_id, keywords_map, components_map, or None if no alternatives.
    """
    # Parse answers JSON
    answers_data = answers_raw
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
        return {"q_id": q_id, "keywords_map": None, "components_map": None, "skipped": True}

    keywords_map = {}
    components_map = {}

    for alt_idx, alt_text in enumerate(alternatives):
        alt_key = f"alternative_{alt_idx}"
        extracted_keywords = extract_keywords(alt_text, top_n=8)
        keywords_map[alt_key] = extracted_keywords

        components_json = generate_expected_components(alt_text)
        components_list = json.loads(components_json) if components_json else []
        components_map[alt_key] = components_list

    return {"q_id": q_id, "keywords_map": keywords_map, "components_map": components_map, "skipped": False}


def backfill_alternative_metadata():
    db = SessionLocal()

    try:
        # Fetch only questions missing keywords — purely ID + answers (lightweight)
        rows = (
            db.query(Questions.id, Questions.answers)
            .filter(Questions.alternative_answer_keywords.is_(None))
            .all()
        )

        total_pending = len(rows)
        print(f"Found {total_pending} questions needing keywords/components.\n")

        if total_pending == 0:
            print("All questions already processed!")
            return

        processed_total = 0
        skipped_total = 0
        error_total = 0
        done = 0

        # Use 4 workers — KeyBERT is CPU-bound but ThreadPoolExecutor still
        # gives a speedup since Python releases the GIL during C-extension calls
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(process_one_question, q_id, answers): q_id
                for q_id, answers in rows
            }

            for future in as_completed(futures):
                q_id = futures[future]
                done += 1
                try:
                    result = future.result()

                    # DB writes happen in the main thread (thread-safe)
                    db.query(Questions).filter(Questions.id == result["q_id"]).update({
                        "alternative_answer_keywords": result["keywords_map"],
                        "alternative_answer_components": result["components_map"],
                    })
                    db.commit()

                    if result["skipped"]:
                        skipped_total += 1
                        status = "SKIP"
                    else:
                        processed_total += 1
                        status = "OK"

                except Exception as e:
                    db.rollback()
                    error_total += 1
                    status = f"ERROR: {e}"

                with print_lock:
                    print(f"[{done}/{total_pending}] Q{q_id}: {status}")

        print(f"\n=== FINAL SUMMARY ===")
        print(f"Processed: {processed_total}")
        print(f"Skipped (no alternatives): {skipped_total}")
        print(f"Errors: {error_total}")
        print(f"Total: {total_pending}")

    except Exception as e:
        print(f"Fatal Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    backfill_alternative_metadata()

