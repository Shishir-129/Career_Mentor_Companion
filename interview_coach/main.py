import traceback
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import librosa
import whisper

from crud.responses import create_response_from_audio
from database.connection import Base, engine, get_db
from routers.users import router as user_router
from routers.questions import router as question_router
from routers.sessions import router as session_router
from routers.responses import router as response_router
from routers import weak_areas
from routers import question_history
from schemas.response import ResponseCreate, ResponseResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Interview Coach API")

# ✅ CORS — allow React dev server (both 5173 and 5174)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
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


# ✅ Pre-warm models on startup to avoid lazy-loading delays
@app.on_event("startup")
async def warmup_models():
    print("\n🔥 Pre-warming AI models on startup...")
    try:
        # Load Whisper
        print("  📻 Loading Whisper model...")
        get_whisper_model()
        print("    ✓ Whisper loaded")
        
        # Load sentence-transformers (used in semantic scoring)
        print("  🔤 Loading sentence-transformers model...")
        from services.semantic_score import get_model
        get_model()
        print("    ✓ Sentence-transformers loaded")
        
        # Load spaCy (used in keyword scoring)
        print("  📝 Loading spaCy model...")
        import spacy
        nlp = spacy.load("en_core_web_sm")
        _ = nlp("warmup test")
        print("    ✓ spaCy loaded")
        
        print("🔥 Model warmup complete - requests should be fast now!\n")
    except Exception as e:
        print(f"⚠️  Model warmup partial failure: {e}")
        print("   (This is OK - models will load on first request)\n")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

_MODEL = None


def get_whisper_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = whisper.load_model("base")
    return _MODEL


def transcribe_audio(file_path: str):
    try:
        print(f"Transcribing with Whisper model: {file_path}")
        
        # ✅ Check file extension - Whisper works best with WAV, MP3, OGG
        file_ext = Path(file_path).suffix.lower()
        if file_ext == ".webm":
            print(f"⚠️  WebM format detected - attempting transcription (may fail without FFmpeg)")
            print(f"    Whisper prefers: WAV, MP3, OGG formats")
        
        model = get_whisper_model()
        # Whisper.transcribe() expects a file path, not audio data
        result = model.transcribe(file_path, fp16=False)
        transcription = result.get("text", "").strip()
        
        if not transcription:
            print(f"⚠️  WARNING: Transcription returned empty string for {file_path}")
            print(f"    This usually means:")
            print(f"    - Audio file is corrupted or in unsupported format ({file_ext})")
            print(f"    - Audio contains no speech")
            print(f"    - File size: {Path(file_path).stat().st_size} bytes")
        else:
            print(f"✓ Transcription complete: {len(transcription)} chars")
        
        return transcription
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        raise


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
        print(f"\n{'='*70}")
        print(f"Processing audio response:")
        print(f"  session_id={session_id}, user_id={user_id}, question_id={question_id}")
        print(f"  filename={audio_file.filename}")
        print(f"{'='*70}")
        
        response = create_response_from_audio(
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
        
        print(f"✓ Response created successfully: id={response.id}")
        return response
    except HTTPException:
        raise  # re-raise FastAPI HTTP exceptions as-is
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR in upload_and_store_transcript:")
        print(f"  Type: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        import traceback as tb
        tb.print_exc()
        
        # Return detailed error message
        error_detail = f"{type(e).__name__}: {str(e)[:200]}"
        print(f"  Returning 500 error: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


if __name__ == "__main__":
    audio_file = "sample.wav"
    try:
        transcription = transcribe_audio(audio_file)
        print("\n--- Transcription Result ---")
        print(transcription)
    except Exception as e:
        print(f"An error occurred: {e}")