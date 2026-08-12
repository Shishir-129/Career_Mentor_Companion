"""
Generate alternative answers for questions with 0 alternatives using Groq API.
Uses Groq to intelligently create contextually relevant alternative answers.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from database.models import Questions

# Try to import Groq SDK
try:
    from groq import Groq
except ImportError:
    print("❌ groq library not installed!")
    print("Install it with: pip install groq")
    exit(1)

# Configure Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY environment variable not set!")
    print("Add GROQ_API_KEY to your .env file")
    exit(1)

client = Groq(api_key=GROQ_API_KEY)
# Use a currently supported Groq model
# gemma-7b-it has been decommissioned, using llama-3.3-70b-versatile instead
GROQ_MODEL = "llama-3.3-70b-versatile"

def generate_alternatives(question_text, ideal_answer):
    """
    Use Groq to generate 2 alternative answers for a question.
    Returns list of 2 alternative answers or empty list if generation fails.
    """
    try:
        prompt = f"""Given the following interview question and ideal answer, generate 2 alternative answers that are:
1. Valid and accurate
2. Different from the ideal answer but covering similar concepts
3. Professional and concise (1-2 sentences)
4. Suitable for a technical/professional interview context

Question: {question_text}

Ideal Answer: {ideal_answer}

Generate exactly 2 alternative answers. Format as:
Alternative 1: [answer]
Alternative 2: [answer]

Only output the alternatives, nothing else."""

        message = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        text = message.choices[0].message.content
        
        # Parse the response
        lines = text.strip().split('\n')
        alternatives = []
        
        for line in lines:
            if line.startswith('Alternative'):
                # Extract the answer part
                answer = line.split(':', 1)[-1].strip()
                if answer:
                    alternatives.append(answer)
        
        return alternatives[:2]  # Return at most 2
        
    except Exception as e:
        print(f"⚠️  Groq error: {e}")
        return []

def populate_alternatives_groq():
    """Generate alternatives for questions with 0 alternatives using Groq"""
    db = SessionLocal()
    
    try:
        # Get all questions
        all_questions = db.query(Questions).all()
        total = len(all_questions)
        
        print(f"Found {total} questions\n")
        
        # Find questions with 0 alternatives
        zero_alt_questions = []
        for q in all_questions:
            if q.answers:
                ans = json.loads(q.answers)
                if len(ans.get('alternatives', [])) == 0:
                    zero_alt_questions.append(q)
            else:
                zero_alt_questions.append(q)
        
        print(f"Found {len(zero_alt_questions)} questions with 0 alternatives")
        print(f"Will generate {len(zero_alt_questions) * 2} alternative answers\n")
        
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
        
        print("\nGenerating alternatives using Groq...\n")
        updated = 0
        errors = 0
        
        for idx, question in enumerate(zero_alt_questions, 1):
            try:
                # Generate alternatives
                alternatives = generate_alternatives(
                    question.question_text,
                    question.ideal_answer
                )
                
                if alternatives:
                    # Update database
                    if question.answers:
                        ans = json.loads(question.answers)
                    else:
                        ans = {"alternatives": []}
                    
                    ans["alternatives"] = alternatives
                    question.answers = json.dumps(ans)
                    db.commit()
                    updated += 1
                    
                    print(f"[{idx}/{len(zero_alt_questions)}] ✓ Generated 2 alternatives")
                else:
                    errors += 1
                    print(f"[{idx}/{len(zero_alt_questions)}] ✗ Failed to generate alternatives")
                
            except Exception as e:
                print(f"[{idx}/{len(zero_alt_questions)}] ✗ Error: {e}")
                errors += 1
                db.rollback()
        
        print(f"\n✅ Complete!")
        print(f"Successfully generated alternatives for: {updated} questions")
        print(f"Failed: {errors} questions")
        
        # Show statistics
        updated_total = db.query(Questions).filter(Questions.answers.isnot(None)).count()
        print(f"\nTotal questions with alternatives: {updated_total}/{total}")
        
        # Sample output
        sample = db.query(Questions).filter(Questions.answers.isnot(None)).first()
        if sample:
            print(f"\n📋 Sample output:")
            print(f"Question: {sample.question_text[:100]}...")
            answers = json.loads(sample.answers)
            print(f"Ideal Answer: {sample.ideal_answer[:80]}...")
            print(f"Alternatives: {answers.get('alternatives', [])[:2]}")
        
    finally:
        db.close()

if __name__ == "__main__":
    populate_alternatives_groq()
