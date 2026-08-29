"""
Migration Script: Fix Missing Session Scores
================================================

Problem: Some sessions have answered > 0 but total_score = NULL
Solution: Calculate scores from responses table and update sessions

This script:
1. Finds all sessions with answered > 0 but total_score IS NULL
2. Calculates their scores from responses
3. Updates sessions table with calculated scores
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
from statistics import mean

# Import your models and connection
import sys
sys.path.insert(0, 'interview_coach')

from database.connection import DATABASE_URL
from database.models import Sessions, Responses, Questions
from routers.sessions import calculate_session_score

def fix_missing_session_scores():
    """Calculate and populate missing total_score values"""
    
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Find all sessions with answered > 0 but total_score IS NULL
        inconsistent_sessions = db.query(Sessions).filter(
            Sessions.answered > 0,
            Sessions.total_score.is_(None)
        ).all()
        
        print(f"\n{'='*70}")
        print(f"Found {len(inconsistent_sessions)} sessions with missing total_score")
        print(f"{'='*70}\n")
        
        fixed_count = 0
        failed_count = 0
        
        for session in inconsistent_sessions:
            try:
                # Get all responses for this session
                responses = db.query(Responses).filter(
                    Responses.session_id == session.id
                ).all()
                
                if not responses:
                    print(f"⚠️  Session {session.id} (user={session.user_id}): No responses found, skipping")
                    continue
                
                # Calculate score using the calculate_session_score function
                overall_score, total_q, answered_count, interview_type = calculate_session_score(responses)
                
                # Update the session
                session.total_score = overall_score
                db.commit()
                
                print(f"✅ Session {session.id:3d} (user={session.user_id:2d}, role={session.role:20s})")
                print(f"   Responses: {len(responses)}, Calculated Score: {overall_score}, Type: {interview_type}")
                fixed_count += 1
                
            except Exception as e:
                print(f"❌ Session {session.id}: Error - {str(e)}")
                failed_count += 1
                continue
        
        print(f"\n{'='*70}")
        print(f"SUMMARY:")
        print(f"  ✅ Fixed: {fixed_count} sessions")
        print(f"  ❌ Failed: {failed_count} sessions")
        print(f"  📊 Total: {fixed_count + failed_count} sessions processed")
        print(f"{'='*70}\n")
        
    finally:
        db.close()


def verify_fix():
    """Verify that all completed sessions now have scores"""
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print(f"\n{'='*70}")
        print("VERIFICATION: Checking for remaining inconsistencies")
        print(f"{'='*70}\n")
        
        # Check for sessions with answered > 0 but total_score IS NULL
        still_missing = db.query(Sessions).filter(
            Sessions.answered > 0,
            Sessions.total_score.is_(None)
        ).all()
        
        if still_missing:
            print(f"⚠️  WARNING: Still {len(still_missing)} sessions with missing scores:")
            for s in still_missing:
                print(f"   Session {s.id}: user={s.user_id}, answered={s.answered}, total_score={s.total_score}")
        else:
            print(f"✅ SUCCESS! All completed sessions now have total_score!")
        
        # Show statistics
        all_sessions = db.query(Sessions).all()
        with_score = db.query(Sessions).filter(Sessions.total_score.isnot(None)).all()
        without_score = db.query(Sessions).filter(Sessions.total_score.is_(None)).all()
        
        print(f"\nStatistics:")
        print(f"  Total sessions: {len(all_sessions)}")
        print(f"  With total_score: {len(with_score)}")
        print(f"  Without total_score: {len(without_score)}")
        
        # Breakdown of without_score
        incomplete = [s for s in without_score if s.answered == 0]
        inconsistent = [s for s in without_score if s.answered > 0]
        
        print(f"\nBreakdown of NULL scores:")
        print(f"  Incomplete sessions (answered=0): {len(incomplete)} ✅ (OK)")
        print(f"  Inconsistent (answered>0, score=NULL): {len(inconsistent)} {'✅' if len(inconsistent) == 0 else '❌'}")
        
        print(f"\n{'='*70}\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SESSION SCORE FIX - Migration Script")
    print("="*70)
    
    # Step 1: Fix missing scores
    fix_missing_session_scores()
    
    # Step 2: Verify the fix
    verify_fix()
    
    print("✅ Migration complete!")
