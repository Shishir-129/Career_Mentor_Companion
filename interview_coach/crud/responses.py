from pathlib import Path
import shutil
from uuid import uuid4
from typing import Callable, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from database.models import Responses
from schemas.response import ResponseCreate, ResponseScoreUpdate
from services.scoring import score_transcript_audio


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

    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        transcript = transcribe_fn(str(saved_path)) if transcribe_fn else ""
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc

    scores = score_transcript_audio(
        transcript=transcript,
        audio_path=str(saved_path),
        question_text=question_text,
        ideal_answer=ideal_answer,
        keywords=keywords,
    )

    response_data = ResponseCreate(
        session_id=session_id,
        user_id=user_id,
        question_id=question_id,
        question_type=question_type,
        topic=topic,
        transcript=transcript,
        audio_file_path=str(saved_path),
    )

    response_data_dict = response_data.model_dump()
    response_data_dict.update(scores)

    return create_response(db, ResponseCreate(**response_data_dict))

    return create_response(db, response_data)


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