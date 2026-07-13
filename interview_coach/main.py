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

# ✅ CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

_MODEL = None


def get_whisper_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = whisper.load_model("base")
    return _MODEL


def transcribe_audio(file_path: str):
    print("Loading and preprocessing audio with Librosa...")
    audio_data, _ = librosa.load(file_path, sr=16000, mono=True)

    print("Transcribing with cached Whisper model...")
    model = get_whisper_model()
    result = model.transcribe(audio_data, fp16=False)

    return result.get("text", "").strip()


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
        raise  # re-raise FastAPI HTTP exceptions as-is
    except Exception as e:
        traceback.print_exc()  # ← prints full traceback to terminal
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


if __name__ == "__main__":
    audio_file = "sample.wav"
    try:
        transcription = transcribe_audio(audio_file)
        print("\n--- Transcription Result ---")
        print(transcription)
    except Exception as e:
        print(f"An error occurred: {e}")