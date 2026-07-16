from pathlib import Path
import json
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from typing import Callable, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from database.models import Questions, Responses
from schemas.response import ResponseCreate, ResponseScoreUpdate
from services.confidence_scoring import analyze_audio, compute_delivery_scores
from services.answer_quality_scorer import compute_answer_quality_score
from services.feedback_generator import generate_feedback


def create_response(db: Session, response: ResponseCreate):
    db_response = Responses(**response.model_dump())
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response


def create_response_from_audio(
    db: Session,
    audio_file: UploadFile,
    session_id: int,
    user_id: int,
    question_id: int,
    question_type: Optional[str] = None,
    topic: Optional[str] = None,
    upload_dir: Optional[Path] = None,
    transcribe_fn: Optional[Callable[[str], str]] = None,
    question_text: Optional[str] = None,
    ideal_answer: Optional[str] = None,
    keywords: Optional[str] = None,
):
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="Audio file is required")

    upload_dir = upload_dir or Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    file_extension = Path(audio_file.filename).suffix or ".wav"
    saved_path = upload_dir / f"{uuid4().hex}{file_extension}"

    # ── 1. Save audio file temporarily ───────────────────────────────────────
    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save audio: {exc}") from exc

    audio_path = str(saved_path)

    try:
        # ✅ Check file was actually saved
        file_size = os.path.getsize(audio_path)
        print(f"📂 Audio file saved: {audio_path} ({file_size} bytes)")
        if file_size == 0:
            raise ValueError("Audio file is empty - browser recording may have failed")
        
        # ── 2. Run Whisper (transcription) + Librosa (audio analysis) in parallel
        #       Both only need the audio file — no dependency between them
        print("🎤 Running transcription and audio analysis in parallel...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_transcript = executor.submit(transcribe_fn, audio_path) if transcribe_fn else None
            future_audio_data = executor.submit(analyze_audio, audio_path)

            transcript = future_transcript.result() if future_transcript else ""
            audio_data = future_audio_data.result()   # {duration_secs, pause_count}

    except Exception as exc:
        print(f"❌ Audio processing failed: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc
    finally:
        # ── 3. Delete audio immediately — it has served its purpose ──────────
        try:
            os.remove(audio_path)
        except OSError:
            pass

    # ✅ Validate transcript was actually generated
    if not transcript or len(transcript.strip()) < 3:
        print(f"⚠️  WARNING: Transcript is empty or too short ({len(transcript) if transcript else 0} chars)")
        print(f"    This could mean:")
        print(f"    - Audio file was corrupted or in unsupported format")
        print(f"    - User did not speak during recording")
        print(f"    - Whisper failed silently")
        
        # Return a response with default values for empty transcript
        db_response = Responses(
            session_id=session_id,
            user_id=user_id,
            question_id=question_id,
            question_type=question_type,
            topic=topic,
            transcript="[No speech detected]",
            semantic_score=0.0,
            keyword_score=0.0,
            completeness_score=0.0,
            answer_quality_score=0.0,
            missed_keywords="",
            confidence_score=0.0,
            grammar_score=0.0,
            speaking_speed=0.0,
            pause_count=0,
            filler_count=0.0,
            llm_feedback="Unable to analyze audio. Please check your microphone and try again with clear speech.",
            strengths=json.dumps([]),
            improvements=json.dumps(["Ensure microphone is working", "Speak clearly during recording"]),
        )
        db.add(db_response)
        db.commit()
        db.refresh(db_response)
        print(f"✅ Empty response saved with ID: {db_response.id}")
        return db_response

    # ── 2. Fetch question data from DB (ideal answer, keywords, components) ──
    print("🔍 Fetching question from database...")
    question = db.query(Questions).filter(Questions.id == question_id).first()
    ideal_answer        = (question.ideal_answer        or "") if question else ""
    keywords_str        = (question.keywords            or "") if question else ""
    expected_components = (question.expected_components or "") if question else ""
    print(f"✓ Question fetched")

    # ── 3. Confidence / delivery scoring ─────────────────────────────────────
    conf = compute_delivery_scores(
        transcript=transcript,
        duration_secs=audio_data["duration_secs"],
        pause_count=audio_data["pause_count"],
    )

    # ── 4. Answer quality scoring (transcript vs ideal answer) ───────────────
    quality = compute_answer_quality_score(
        user_answer=transcript,
        ideal_answer=ideal_answer,
        keywords_str=keywords_str,
        expected_components_json=expected_components,
    )

    # ── 5. Generate feedback ──────────────────────────────────────────────────
    feedback = generate_feedback(
        answer_quality_score=quality["answer_quality_score"],
        quality_label=quality["quality_label"],
        semantic_score=quality["semantic_score"],
        keyword_score=quality["keyword_score"],
        completeness_score=quality["completeness_score"],
        missed_keywords=quality["missed_keywords"],
        components_missing=quality["components_missing"],
        coaching_tips=quality["coaching_tips"],
        confidence_score=conf["confidence_score"],
        grammar_score=conf["grammar_score"],
        speaking_speed=conf["speaking_speed"],
        filler_count=conf["filler_count"],
        pause_count=conf["pause_count"],
        transcript=transcript,
    )

    # ── 6. Save response to database ─────────────────────────────────────────
    db_response = Responses(
        session_id=session_id,
        user_id=user_id,
        question_id=question_id,
        question_type=question_type,
        topic=topic,
        transcript=transcript,
        # audio_file_path intentionally not stored — file is deleted after processing
        # Answer quality — WHAT was said
        semantic_score=quality["semantic_score"],
        keyword_score=quality["keyword_score"],
        completeness_score=quality["completeness_score"],
        answer_quality_score=quality["answer_quality_score"],
        missed_keywords=", ".join(quality["missed_keywords"]),
        # Confidence / delivery — HOW it was said
        confidence_score=conf["confidence_score"],
        grammar_score=conf["grammar_score"],
        speaking_speed=conf["speaking_speed"],
        pause_count=conf["pause_count"],
        filler_count=conf["filler_count"],
        # Feedback
        llm_feedback=feedback["narrative_feedback"],
        strengths=json.dumps(feedback["strengths"]),
        improvements=json.dumps(feedback["improvements"]),
    )

    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response


def get_response(db: Session, response_id: int):
    return db.query(Responses).filter(Responses.id == response_id).first()


def get_responses_by_session(db: Session, session_id: int):
    return db.query(Responses).filter(Responses.session_id == session_id).all()


def get_responses_by_user(db: Session, user_id: int):
    return db.query(Responses).filter(Responses.user_id == user_id).all()


def update_response_score(db: Session, response_id: int, data: ResponseScoreUpdate):
    response = get_response(db, response_id)
    if not response:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(response, key, value)

    db.commit()
    db.refresh(response)
    return response


def delete_response(db: Session, response_id: int):
    response = get_response(db, response_id)
    if not response:
        return None
    db.delete(response)
    db.commit()
    return response