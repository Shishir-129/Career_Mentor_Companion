"""
Generate multiple acceptable answers for each question using semantic similarity.
Uses sentence-transformers to find similar questions and reuse their answers.
No API calls, completely free, runs in 2-3 minutes for 500 questions.
"""

import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Questions
import sys

# Load the sentence transformer model
print("Loading sentence-transformers model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✓ Model loaded\n")

def encode_questions(questions):
    """Convert all question texts to embeddings"""
    print(f"Encoding {len(questions)} questions...")
    question_texts = [q.question_text for q in questions]
    embeddings = model.encode(question_texts, show_progress_bar=True)
    return embeddings

def find_similar_questions(embeddings, threshold=0.80):
    """
    Find similar question pairs using cosine similarity.
    Returns: dict mapping question_index -> [list of similar question indices]
    """
    print("\nCalculating similarity scores...")
    similarity_matrix = cosine_similarity(embeddings)
    
    similar_pairs = {}
    for i in range(len(embeddings)):
        similar_indices = []
        for j in range(len(embeddings)):
            if i != j and similarity_matrix[i][j] >= threshold:
                similar_indices.append((j, similarity_matrix[i][j]))
        
        # Sort by similarity score (highest first)
        similar_indices.sort(key=lambda x: x[1], reverse=True)
        similar_pairs[i] = similar_indices
    
    return similar_pairs

def build_answers_json(question, similar_questions_data):
    """
    Build JSON structure with ideal answer and alternatives from similar questions.
    
    Structure:
    {
        "ideal": "ideal answer text",
        "alternatives": ["answer1", "answer2", ...]
    }
    """
    alternatives = []
    
    # Add alternative answers from similar questions
    for similar_q_idx, similarity_score in similar_questions_data[:3]:  # Top 3 similar
        similar_q = similar_questions_data[similar_q_idx] if isinstance(similar_questions_data[similar_q_idx], tuple) else None
        if similar_q and similar_q.ideal_answer and similar_q.ideal_answer != question.ideal_answer:
            alternatives.append(similar_q.ideal_answer)
    
    # Remove duplicates while preserving order
    alternatives = list(dict.fromkeys(alternatives))
    
    return {
        "ideal": question.ideal_answer,
        "alternatives": alternatives
    }

def populate_answers():
    """Main function to populate answers column for all questions"""
    db = SessionLocal()
    
    try:
        # Get all questions first to check totals
        all_questions_db = db.query(Questions).all()
        total_db = len(all_questions_db)
        
        if total_db == 0:
            print("❌ No questions found in database!")
            return
        
        print(f"Found {total_db} questions in database\n")
        
        # Filter to get ONLY questions with 0 alternatives
        print("Filtering for questions with 0 alternatives...")
        all_questions = []
        for q in all_questions_db:
            if q.answers:
                ans = json.loads(q.answers)
                if len(ans.get('alternatives', [])) == 0:
                    all_questions.append(q)
            else:
                all_questions.append(q)
        
        total = len(all_questions)
        with_answers = total_db - total
        
        print(f"✓ Questions with 0 alternatives: {total}")
        print(f"✓ Questions with existing alternatives: {with_answers}\n")
        
        if total == 0:
            print("✅ All questions already have alternatives!")
            return
        
        # Step 1: Encode only the zero-alternative questions
        embeddings = encode_questions(all_questions)
        
        # Step 2: Find similar questions - Layer 1 (strict threshold 0.80)
        print("\n📊 Layer 1: Finding matches with threshold 0.80...")
        similar_pairs_layer1 = find_similar_questions(embeddings, threshold=0.80)
        
        layer1_count = sum(1 for v in similar_pairs_layer1.values() if v)
        print(f"✓ Layer 1 found {layer1_count} questions with similar matches")
        
        # Step 2b: Find similar questions - Layer 2 (lenient threshold 0.75 for fallback)
        print("📊 Layer 2: Finding matches with threshold 0.75 (fallback)...")
        similar_pairs_layer2 = find_similar_questions(embeddings, threshold=0.75)
        
        layer2_count = sum(1 for v in similar_pairs_layer2.values() if v)
        print(f"✓ Layer 2 found {layer2_count} questions with similar matches")
        
        # Step 2c: Find similar questions - Layer 3 (very lenient threshold 0.70 for last resort)
        print("📊 Layer 3: Finding matches with threshold 0.70 (last resort)...")
        similar_pairs_layer3 = find_similar_questions(embeddings, threshold=0.70)
        
        layer3_count = sum(1 for v in similar_pairs_layer3.values() if v)
        print(f"✓ Layer 3 found {layer3_count} questions with similar matches\n")
        
        # Step 3: Populate answers
        print("Populating answers column...\n")
        updated = 0
        layer2_used = 0
        layer3_used = 0
        
        for idx, question in enumerate(all_questions, 1):
            try:
                # Try Layer 1 first (threshold 0.80)
                similar_q_indices = similar_pairs_layer1.get(idx - 1, [])
                
                # Get similar question objects
                similar_q_objects = []
                for sim_idx, score in similar_q_indices:
                    similar_q_objects.append((all_questions[sim_idx], score))
                
                # Build alternatives list (store only alternatives, ideal_answer is separate)
                alternatives = []
                
                # Add alternatives from similar questions
                for similar_q, score in similar_q_objects:
                    if similar_q.ideal_answer and similar_q.ideal_answer != question.ideal_answer:
                        alternatives.append(similar_q.ideal_answer)
                
                # Remove duplicates
                alternatives = list(dict.fromkeys(alternatives))
                
                # Layer 2 Fallback: If Layer 1 found nothing, try Layer 2 (threshold 0.75)
                if len(alternatives) == 0:
                    similar_q_indices_layer2 = similar_pairs_layer2.get(idx - 1, [])
                    
                    for sim_idx, score in similar_q_indices_layer2:
                        similar_q = all_questions[sim_idx]
                        if similar_q.ideal_answer and similar_q.ideal_answer != question.ideal_answer:
                            alternatives.append(similar_q.ideal_answer)
                    
                    # Remove duplicates
                    alternatives = list(dict.fromkeys(alternatives))
                    
                    if alternatives:
                        layer2_used += 1
                
                # Layer 3 Fallback: If Layer 2 found nothing, try Layer 3 (threshold 0.70)
                if len(alternatives) == 0:
                    similar_q_indices_layer3 = similar_pairs_layer3.get(idx - 1, [])
                    
                    for sim_idx, score in similar_q_indices_layer3:
                        similar_q = all_questions[sim_idx]
                        if similar_q.ideal_answer and similar_q.ideal_answer != question.ideal_answer:
                            alternatives.append(similar_q.ideal_answer)
                    
                    # Remove duplicates
                    alternatives = list(dict.fromkeys(alternatives))
                    
                    if alternatives:
                        layer3_used += 1
                
                # Store only alternatives as JSON (ideal_answer is stored in ideal_answer column)
                question.answers = json.dumps({"alternatives": alternatives})
                db.commit()
                updated += 1
                
                # Progress update every 50 questions
                if idx % 50 == 0:
                    num_alts = len(alternatives)
                    print(f"[{idx}/{total}] ✓ Updated | Alternatives: {num_alts}")
                
            except Exception as e:
                print(f"[{idx}/{total}] ✗ Error: {e}")
                db.rollback()
        
        print(f"\n✅ Complete! Updated {updated}/{total} questions")
        print(f"Layer 1 matches: {sum(1 for v in similar_pairs_layer1.values() if v) - layer2_used - layer3_used} questions")
        print(f"Layer 2 fallback used for: {layer2_used} questions")
        print(f"Layer 3 fallback used for: {layer3_used} questions")
        
        # Show statistics
        with_alts = db.query(Questions).filter(Questions.answers.isnot(None)).count()
        print(f"Questions with alternatives: {with_alts}")
        
        # Sample output
        sample = db.query(Questions).filter(Questions.answers.isnot(None)).first()
        if sample:
            print(f"\n📋 Sample output:")
            print(f"Question: {sample.question_text[:60]}...")
            print(f"Ideal Answer: {sample.ideal_answer[:60]}...")
            answers = json.loads(sample.answers)
            print(f"Alternatives: {len(answers['alternatives'])} found")
            if answers['alternatives']:
                print(f"  Example: {answers['alternatives'][0][:60]}...")
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Multiple Answer Generator using Semantic Similarity")
    print("=" * 60 + "\n")
    
    populate_answers()
