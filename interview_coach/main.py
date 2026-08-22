import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import whisper

from crud.responses import create_response_from_audio
from database.connection import Base, engine, get_db
from routers.users import router as user_router
from routers.questions import router as question_router
from routers.sessions import router as session_router
from routers.responses import router as response_router
from routers import weak_areas
from routers import question_history
from routers import ratings
from schemas.response import ResponseResponse

log = logging.getLogger("uvicorn.error")

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm all AI models on startup to avoid first-request latency."""
    log.info("Loading AI models...")
    try:
        get_whisper_model()
        log.info("Whisper ready")

        from services.semantic_score import get_model
        get_model()
        log.info("Sentence-transformers ready")

        import spacy
        spacy.load("en_core_web_sm")
        log.info("spaCy ready")

        log.info("All models loaded — API is ready")
    except Exception as exc:
        log.warning("Model warmup partial failure: %s (will load on first request)", exc)
    yield


app = FastAPI(title="Interview Coach API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # local
        "http://localhost:5174",  # local
        "",  # deployed: set this to the deployed frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(question_router)
app.include_router(session_router)
app.include_router(response_router)
app.include_router(weak_areas.router)
app.include_router(question_history.router)
app.include_router(ratings.router)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

_MODEL = None


def get_whisper_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = whisper.load_model("base")
    return _MODEL


def transcribe_audio(file_path: str) -> str:
    model = get_whisper_model()
    result = model.transcribe(file_path, fp16=False)
    transcription = result.get("text", "").strip()
    if not transcription:
        log.warning("Empty transcription for %s (size: %d bytes)", file_path, Path(file_path).stat().st_size)
    return transcription


@app.post("/responses/upload-audio", response_model=ResponseResponse)
async def upload_and_store_transcript(
    session_id: int = Form(...),
    user_id: int = Form(...),
    question_id: int = Form(...),
    question_type: str | None = Form(None),
    topic: str | None = Form(None),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        return create_response_from_audio(
            db=db,
            audio_file=audio_file,
            session_id=session_id,
            user_id=user_id,
            question_id=question_id,
            question_type=question_type,
            topic=topic,
            upload_dir=UPLOAD_DIR,
            transcribe_fn=transcribe_audio,
        )
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Error processing audio response")
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {str(exc)[:200]}")