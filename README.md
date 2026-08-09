# Interview Coach

An AI-powered mock interview platform for Data Science roles. Candidates register, select a role, difficulty and experience level, answer spoken questions, and receive instant scoring and coaching feedback on both **content quality** and **delivery confidence**.

---

## Project Structure

```
minor_project/
├── frontend/                   # React + Vite frontend
│   └── src/
│       ├── api/
│       │   ├── config.js       # BASE_URL + auth helpers (getAuth, getUserId)
│       │   └── interviewApi.js # All API calls in one place
│       ├── components/
│       │   └── Sidebar.jsx     # Navigation sidebar with logout
│       └── pages/
│           ├── Login           # Login & register
│           ├── NewInterview    # Configure role, level, difficulty, type
│           ├── StartInterview  # Record answers, view per-question feedback
│           ├── Dashboard       # Scores, performance trend chart, session history
│           ├── WeakAreas       # Skill breakdown with improvement tips
│           └── Settings        # Account profile view
│
└── interview_coach/            # FastAPI backend
    ├── main.py                 # App entry point, Whisper transcription, model warmup
    ├── database/
    │   ├── connection.py       # SQLAlchemy engine & session
    │   └── models.py           # User, Questions, Sessions, Responses
    ├── routers/                # API route handlers (one file per resource)
    ├── crud/                   # Database operations (one file per model)
    ├── schemas/                # Pydantic request/response models
    ├── services/               # AI scoring & feedback logic
    │   ├── semantic_score.py       # sentence-transformers cosine similarity
    │   ├── keyword_score.py        # spaCy lemmatized keyword matching
    │   ├── completeness_score.py   # Structural component detection
    │   ├── answer_quality_scorer.py # Aggregates above three (50/30/20)
    │   ├── confidence_scoring.py   # Grammar, pace, fillers, pauses via librosa
    │   ├── feedback_generator.py   # Score-derived coaching narrative
    │   ├── question_generator.py   # Greedy semantic diversity selection
    │   ├── keyword_extractor.py    # KeyBERT extraction (used by seed scripts)
    │   └── components_generator.py # Detects expected components (used by seeds)
    └── scripts/                # One-time DB utilities (seed, migrate, check)
```

---

## How It Works

```
User records answer (browser mic)
        │
        ▼
POST /responses/upload-audio
        │
        ├─── [parallel] ─── Whisper (speech → text)
        │                   Librosa (audio duration + pause detection)
        │
        ├─── Answer Quality Score (70% of final)
        │       ├─ Semantic     50%  (sentence-transformers cosine similarity)
        │       ├─ Keywords     30%  (spaCy lemmatized matching)
        │       └─ Completeness 20%  (structural component detection)
        │
        ├─── Confidence Score (30% of final)
        │       ├─ Grammar      35%  (TTR + sentence length + repetition)
        │       ├─ Filler words 30%  (um, uh, basically, literally…)
        │       ├─ Speaking pace 20% (WPM — ideal: 120–155)
        │       └─ Pauses       15%  (hesitation gaps > 1s via librosa)
        │
        └─── Score-derived coaching feedback paragraph
                    │
                    ▼
             Stored in PostgreSQL → displayed in frontend
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | **3.12.10** (PyTorch is not compatible with 3.13/3.14) |
| Node.js | 18+ |
| PostgreSQL | Any (Neon cloud or local) |
| Disk space | ~2 GB (ML models) |

---

## Backend Setup

```powershell
cd interview_coach

# 1. Create virtual environment with Python 3.12
python3.12 -m venv venv_py312
.\venv_py312\Scripts\Activate.ps1

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Download spaCy language model
python -m spacy download en_core_web_sm

# 4. Configure environment
copy .env.example .env
# Edit .env and set DATABASE_URL to your PostgreSQL connection string

# 5. Start the server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The server logs will show `All models loaded — API is ready` once Whisper, sentence-transformers, and spaCy have finished loading (~30–60 s on first start).

---

## Frontend Setup

```powershell
cd frontend

# 1. Install dependencies
npm install

# 2. Start dev server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/users/register` | Register a new user |
| `POST` | `/users/login` | Login — returns user profile |
| `POST` | `/sessions/` | Start a new interview session |
| `PATCH` | `/sessions/{id}/end` | Mark session as completed |
| `GET` | `/sessions/user/{id}/history` | All sessions with aggregated scores |
| `POST` | `/questions/for-session` | Fetch diverse questions for role + level + difficulty |
| `POST` | `/responses/upload-audio` | Submit audio answer → full scoring |
| `GET` | `/responses/session/{id}` | All responses for a session |
| `GET` | `/weak-areas/user/{id}` | User's identified weak topics |
| `GET` | `/question-history/user/{id}` | Questions previously seen |

Full interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Scoring System

### Answer Quality Score (0–100)

| Component | Weight | Method |
|---|---|---|
| Semantic similarity | 50% | Cosine similarity via `all-MiniLM-L6-v2` |
| Keyword coverage | 30% | spaCy lemmatized matching against expected keywords |
| Structural completeness | 20% | Pattern detection for definition, example, explanation, etc. |

### Confidence Score (0–100)

| Component | Weight | Method |
|---|---|---|
| Grammar quality | 35% | Type-token ratio + sentence length naturalness |
| Filler word rate | 30% | "um", "uh", "basically", "literally", etc. |
| Speaking pace | 20% | Words per minute (ideal: 120–155 WPM) |
| Pause frequency | 15% | Hesitation gaps > 1 s detected by librosa |

### Final Score

`Final = Answer Quality × 0.70 + Confidence × 0.30`

### Labels

| Score | Label |
|---|---|
| ≥ 85 | Excellent |
| ≥ 65 | Good |
| ≥ 45 | Average |
| < 45 | Poor |

---

## Supported Roles & Types

**Roles:** Data Analyst · Data Scientist · DevOps Engineer

**Experience levels:** Fresher (0–1 yr) · Junior (1–3 yr) · Mid-level (3–5 yr) · Senior (5+ yr)

**Interview types:** Technical · Behavioral · Theoretical · Mixed

---

## Tech Stack

### Backend
- **FastAPI** — async REST API
- **SQLAlchemy 2** — ORM with PostgreSQL
- **OpenAI Whisper** (base, local) — speech-to-text
- **sentence-transformers** (`all-MiniLM-L6-v2`, local) — semantic scoring + question diversity selection
- **spaCy** (`en_core_web_sm`, local) — keyword lemmatization
- **KeyBERT** — keyword extraction at seeding time (result stored in DB)
- **librosa** — audio duration + hesitation pause detection
- **pwdlib** (argon2) — password hashing

### Frontend
- **React 19** + **Vite**
- **React Router** — client-side routing with auth guards
- **Recharts** — performance trend chart
- **react-icons** — UI icons

---

## Notes

- **Auth** — email + password login. Password hashed with argon2. User profile stored in `localStorage` after login. Sign out clears the session.
- **Question selection** — greedy semantic diversity using `all-MiniLM-L6-v2` ensures each session covers different topics. Questions with high `times_asked` are deprioritized so content stays fresh across sessions.
- **Coaching feedback** — score-derived rule-based narrative. Not LLM-generated. Reads the actual numeric scores and identified gaps to produce specific, actionable paragraphs.
- **Audio** — browser sends WebM; Whisper handles it directly. File is deleted immediately after transcription.
- **Model warmup** — Whisper, sentence-transformers, and spaCy load at startup via the `lifespan` handler, so all responses after the first are fast.

```bash
# Create
python3.12 -m venv venv_py312

# Activate (Windows)
.\venv_py312\Scripts\Activate.ps1

# Activate (macOS/Linux)
source venv_py312/bin/activate

# Activate (macOS/Linux)
source venv_py312/bin/activate
```

### 4. Install dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Note:** First time installation will download ML models (~540MB). This takes 5-10 minutes.

### 5. Configure environment variables

Copy the environment template:
```bash
cp interview_coach/.env.example interview_coach/.env
```

Edit `.env` with your settings:
```env
DATABASE_URL=postgresql://user:password@host/dbname
DEBUG=False
```

---

## Quick Start

### Start Backend (FastAPI)

```powershell
# Windows
cd interview_coach
.\venv_py312\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Backend: http://localhost:8000
Docs: http://localhost:8000/docs

### Start Frontend (React + Vite)

```bash
# In new terminal
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5174

---

## Detailed Documentation

- **Backend Setup:** [interview_coach/README_BACKEND.md](interview_coach/README_BACKEND.md)
- **Frontend Setup:** [frontend/README.md](frontend/README.md)

---

## 📦 Project Structure

```
.
├── interview_coach/          # FastAPI backend
│   ├── main.py              # App entry point
│   ├── requirements.txt      # Python dependencies
│   ├── README_BACKEND.md    # Detailed backend docs
│   ├── .env.example         # Environment template
│   ├── .python-version      # Python 3.12 requirement
│   ├── crud/                # Database operations
│   ├── database/            # SQLAlchemy models
│   ├── routers/             # API endpoints
│   ├── schemas/             # Pydantic models
│   └── services/            # ML services
│
├── frontend/                # React + Vite
│   ├── src/
│   ├── package.json
│   └── README.md
│
└── README.md               # This file
```

---

## Troubleshooting

### Python Version Error

```powershell
# If you see "python3.12 not found"
python --version  # Check your current version

# Install Python 3.12
winget install Python.Python.3.12
```

### "ERR_CONNECTION_RESET" on audio upload

This means Python 3.14+ is running. Switch to Python 3.12:

```powershell
.\venv_py312\Scripts\python.exe -m uvicorn main:app --reload
```

### Models download very slowly

- **First run:** 5-10 minutes (normal, downloads 540MB of models)
- **Cached:** Models load from RAM on subsequent requests
- Check disk space: needs ~2GB free

### Database connection fails

1. Verify DATABASE_URL in `.env`
2. Check PostgreSQL is running (or Neon is accessible)
3. Try local test: `psql -U user -d dbname -h localhost`

---

## Development Notes

- **Python version required:** 3.12.10 (enforced via .python-version)
- **Virtual environment:** venv_py312
- **Backend:** FastAPI + Uvicorn + SQLAlchemy
- **Frontend:** React 19 + Vite
- **Database:** PostgreSQL (Neon)
- **ML Models:** Whisper, sentence-transformers, FLAN-T5, spaCy

---

## Running the API

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

---

## API Documentation

FastAPI provides interactive docs automatically:

| Tool | URL |
|------|-----|
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |

---

## API Endpoints

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/register` | Register a new user |
| GET | `/users/` | Get all users |
| GET | `/users/{user_id}` | Get a user by ID |
| DELETE | `/users/{user_id}` | Delete a user |

### Register a User

**POST** `/users/register`

Request body:
```json
{
  "fullname": "Sagar Paudel",
  "email": "sagar@gmail.com",
  "password": "yourpassword"
}
```

Response:
```json
{
  "id": 1,
  "fullname": "Sagar Paudel",
  "email": "sagar@gmail.com"
}
```

---

## Project Structure

```
interview_coach/
├── main.py               # App entry point
├── .env                  # Environment variables
├── requirements.txt      # Dependencies
├── crud/
│   ├── __init__.py
│   └── users.py          # Database operations
├── database/
│   ├── __init__.py
│   ├── connection.py     # Database connection
│   └── models.py         # SQLAlchemy models
├── routers/
│   ├── __init__.py
│   └── users.py          # API routes
└── schemas/
    ├── __init__.py
    └── user.py           # Pydantic schemas
```

---

## Database Setup

The tables are created automatically on server startup via SQLAlchemy.

If you need to reset the database, run the following in your Neon SQL Editor:

```sql
DROP TABLE IF EXISTS users;
```

Then restart the server to recreate the tables.