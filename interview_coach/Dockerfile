FROM python:3.12-slim

WORKDIR /app

# System dependencies needed for librosa/soundfile/whisper (audio processing) and building some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching — only reinstalls if requirements.txt changes)
# torch is installed separately from the CPU-only wheel index first, so the requirements.txt
# install doesn't pull in ~2GB of unnecessary NVIDIA CUDA packages (this machine has no GPU).
# requirements.txt already pins the en_core_web_sm wheel directly (works around a spaCy 3.7.2
# bug where `spacy download` produces a malformed/404ing URL).
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Bake Whisper "base" model into the image at build time (avoids slow first-request download)
RUN python -c "import whisper; whisper.load_model('base')"

# Pre-download sentence-transformers model used in services/semantic_score.py
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the rest of the application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
