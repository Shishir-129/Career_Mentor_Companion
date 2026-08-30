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
    │   └── models.py           # User, Questions, Sessions, Responses, SessionRatings
    ├── routers/                # API route handlers (one file per resource)
    ├── crud/                   # Database operations (one file per model)
    ├── schemas/                # Pydantic request/response models
    ├── services/               # AI scoring & feedback logic
    │   ├── semantic_score.py           # sentence-transformers cosine similarity; picks best of ideal + alternatives
    │   ├── keyword_score.py            # spaCy lemmatized keyword matching
    │   ├── completeness_score.py       # Structural component detection + parroting guard
    │   ├── answer_quality_scorer.py    # Aggregates above three (50/30/20); dynamic weights for no-keyword questions
    │   ├── confidence_scoring.py       # Grammar/substance, pace, pauses (filler kept at 5% — Whisper strips them)
    │   ├── feedback_generator.py       # Score-derived coaching narrative
    │   ├── question_generator.py       # Greedy semantic diversity + reference-answer validity gate
    │   ├── keyword_extractor.py        # KeyBERT extraction (used at seed time)
    │   └── components_generator.py     # Detects expected answer components
    └── scripts/
        ├── scrape_and_seed.py      # Multi-source Q&A scraper + DB seeder
        └── generate_qna_docx.py    # Exports verified Q&A bank to Word document
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
        │       │
        │       ├─ Best-reference selection: picks ideal answer OR best-matching
        │       │  alternative (up to 2 stored) via cosine similarity
        │       │
        │       ├─ Semantic     50%  (sentence-transformers cosine similarity)
        │       ├─ Keywords     30%  (spaCy lemmatized matching against best-ref keywords)
        │       │               → redistributed to semantic (80/20) when no keywords defined
        │       └─ Completeness 20%  (component detection; parroting capped at 20)
        │
        ├─── Confidence Score (30% of final)
        │       ├─ Grammar/Substance 45%  (original content depth + TTR + sentence naturalness)
        │       ├─ Speaking pace     25%  (WPM — ideal: 120–155)
        │       ├─ Pause frequency   25%  (hesitation gaps > 1 s via librosa)
        │       └─ Filler words       5%  (Whisper strips fillers → signal is unreliable at high weight)
        │
        └─── Score-derived coaching feedback paragraph
                    │
                    ▼
             Stored in DB → displayed in frontend
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | **3.12.10** |
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

The server logs `All models loaded — API is ready` once Whisper, sentence-transformers, and spaCy have finished loading (~30–60 s on first start).

---

## Frontend Setup

```powershell
cd frontend
npm install
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
| `PATCH` | `/sessions/{id}/end` | Mark session as completed, triggers weak-area update |
| `GET` | `/sessions/user/{id}/history` | All sessions with aggregated scores |
| `POST` | `/questions/for-session` | Fetch diverse questions for role + level + difficulty |
| `POST` | `/responses/upload-audio` | Submit audio answer → full scoring pipeline |
| `GET` | `/responses/session/{id}` | All responses for a session |
| `GET` | `/weak-areas/user/{id}` | User's skill weak areas (running averages) |
| `POST` | `/ratings/` | Submit 1–5 star session rating |
| `GET` | `/question-history/user/{id}` | Questions previously seen by user |

Full interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Scoring System

### Answer Quality Score (0–100)

| Component | Weight | Method |
|---|---|---|
| Semantic similarity | **50%** | Cosine similarity via `all-MiniLM-L6-v2` against best-matching reference |
| Keyword coverage | **30%** | spaCy lemmatized matching — *redistributed to semantic when no keywords defined* |
| Structural completeness | **20%** | Component pattern detection + parroting guard |

**Multi-reference evaluation:** Each question stores an ideal answer and up to two validated alternative answers. The semantic scorer picks the best-matching reference (highest cosine similarity) and all subsequent scoring uses *that reference's* keywords and components. This prevents penalising a candidate for giving a valid alternative explanation.

**Behavioural/no-keyword questions:** When a question has no keyword list (e.g., HR or open-ended questions), applying 30% keyword weight with KW = 0 would unfairly cap the score at 70. The pipeline detects this and uses `AQ = SEM × 0.80 + COMP × 0.20` instead.

### Confidence Score (0–100)

| Component | Weight | Method |
|---|---|---|
| Grammar / Substance | **45%** | Content originality vs question, type-token ratio, sentence length naturalness |
| Speaking pace | **25%** | Words per minute (ideal band: 120–155 WPM) |
| Hesitation pauses | **25%** | Silence gaps > 1 s per minute, detected from raw audio via librosa |
| Filler word rate | **5%** | Per 100 words — kept low because Whisper ASR strips most fillers from transcripts |

### Overall Score (Per-Question & Session Level)

The overall score calculation differs based on **interview type**:

#### Technical Questions (70% Quality, 30% Confidence)
```
OVERALL = Answer Quality × 0.70 + Confidence × 0.30
```
Content quality is weighted more heavily, reflecting how technical interviewers prioritise domain knowledge.

#### Behavioral Questions (70% Confidence, 30% Quality)
```
OVERALL = Confidence × 0.70 + Answer Quality × 0.30
```
Delivery and storytelling (STAR components) are weighted more heavily, reflecting how behavioral interviewers prioritise communication and soft skills.

#### Session Score (Average of All Answers)
```
SESSION_SCORE = Average(question_1_overall, question_2_overall, ..., question_5_overall)
```

The session-level score is **always recalculated** when fetched from the API using the latest weights and formulas. This ensures:
- ✅ Fresh calculations reflect any weight changes
- ✅ No stale data from database
- ✅ Consistent scoring even if question type changes
- ✅ Accurate session history for frontend display

**API Endpoint:** `GET /sessions/user/{user_id}/history`
- Returns: `session_id`, `answered` (count of questions completed), `total_questions` (always 5), `overall_score` (average), `interview_type`, and per-component breakdowns

### STAR Components (Behavioral Questions Only)

For behavioral/HR questions, completeness is evaluated using the **STAR framework**:
- **S**ituation — Context/background of the scenario
- **T**ask — Your responsibility or challenge
- **A**ction — Specific steps you took
- **R**esult — Outcome and lessons learned

**STAR Detection:**
- Pattern-matching against 57 trigger phrases (e.g., "when I faced", "my role was", "I decided to", "the result was")
- Case-insensitive substring matching across answer transcript
- Score = (components_found / 4) × 100
  - All 4 components = 100 (excellent STAR storytelling)
  - 3 components = 75 (good)
  - 2 components = 50 (fair)
  - 1 component = 25 (weak)
  - 0 components = 0 (missing STAR)

**Behavioral Answer Quality Adjustments:**
- `semantic_score = 0` (no ideal answer comparison — personal stories are valid)
- `keyword_score = 0` (behavioral answers don't require technical vocabulary)
- `completeness_score = 100%` weight (STAR structure is the primary signal)

### Completeness Score — Technical vs. Behavioral

#### Technical Questions (Expected Components)
When a technical question has `expected_components` defined (e.g., ["definition", "example", "formula"]):
- Detects presence of expected components via pattern matching
- Applies parroting guard (if > 70% token overlap with question, caps score at 20)
- Score = 0–100 based on component coverage

#### Behavioral Questions (STAR Components)
See STAR Components section above.

### Labels

| Score | Label |
|---|---|
| ≥ 85 | Excellent |
| ≥ 65 | Good |
| ≥ 45 | Average |
| < 45 | Poor |

---

## Weak-Area Tracking

After every completed session, the weak-area service updates the `UserWeakAreas` table using a **weighted running average** — not a simple overwrite:

```
new_avg = (old_avg × old_count + session_avg × session_count) / (old_count + session_count)
```

This ensures all historical sessions proportionally influence the running score. The Weak Areas page displays per-topic averages across five dimensions (semantic, keyword, completeness, confidence, grammar) ranked from lowest to highest.

---

## Q&A Database

Each question stores: `ideal_answer`, `answers` JSON (`{"ideal": "...", "alternatives": ["...", "..."]}`), `keywords`, `alternative_answer_keywords`, `expected_components`, `alternative_answer_components`, `difficulty`, `topic`, and `experience_level`.

### Sources

| # | Repository / Site | Topics | Questions |
|---|---|---|---|
| 1 | [alexeygrigorev/data-science-interviews](https://github.com/alexeygrigorev/data-science-interviews) | ML, DL, NLP, Clustering, Time Series | ~166 |
| 2 | [youssefHosni/Data-Science-Interview-Questions-Answers](https://github.com/youssefHosni/Data-Science-Interview-Questions-Answers) | ML, Statistics, Probability, Python, DL, SQL | ~100 |
| 3 | [iamtodor/data-science-interview-questions-and-answers](https://github.com/iamtodor/data-science-interview-questions-and-answers) | Regularization, Feature Selection, Metrics | ~32 |
| 4 | [kojino/120-Data-Science-Interview-Questions](https://github.com/kojino/120-Data-Science-Interview-Questions) | Probability, Statistical Inference, EDA, Predictive Modeling | ~115 |
| 5 | roadmap.sh/questions/data-science | General DS | varies |
| 6 | Expert-curated | SQL, Python, Deep Learning, NLP, MLOps, Feature Engineering | ~32 |

**Total verified questions in DB: ~450+** across 20 topic areas.

### Question Selection Pipeline

1. **Filter** — role + experience level + question type + difficulty (4-pass progressive fallback)
2. **Reference validity gate** — questions with neither a valid `ideal_answer` nor at least one alternative are rejected before selection
3. **Semantic diversity** — greedy algorithm selects questions whose embeddings are maximally different from each other
4. **Freshness priority** — unseen questions get +0.15 bonus; heavily repeated questions get up to −0.30 penalty

---

## Scoring Robustness

### Anti-Gaming Protections

| Scenario | Completeness | Confidence |
|---|---|---|
| Repeat the question back | ≤ 20 (parroting guard caps at 20 if > 70% token overlap) | ≤ 32 (substance ≈ 0) |
| Say random technical words | 0–15 (no ideal-keyword overlap) | ≤ 28 (word-count gate) |
| Very short answer (< 8 words) | `word_count × 2` max | ≤ 28 (hard cap) |
| Good substantive answer | 55–100 | 60–90 |

---

## Supported Roles & Types

**Roles:** Data Analyst · Data Scientist

**Experience levels:** Fresher (0–1 yr) · Junior (1–3 yr) · Mid-level (3–5 yr) · Senior (5+ yr)

**Interview types:** Technical · Behavioral · Theoretical · Mixed

---

## Tech Stack

### Backend
- **FastAPI** — async REST API
- **SQLAlchemy 2** — ORM with PostgreSQL/SQLite
- **OpenAI Whisper** (`base`, local) — speech-to-text
- **sentence-transformers** (`all-MiniLM-L6-v2`, local) — semantic scoring + question diversity selection
- **spaCy** (`en_core_web_sm`, local) — keyword lemmatization
- **KeyBERT** — keyword extraction at seeding time (stored in DB)
- **librosa** — audio duration + hesitation pause detection
- **python-docx** — Q&A bank Word document export
- **pwdlib** (argon2) — password hashing

### Frontend
- **React 18** + **Vite**
- **Plus Jakarta Sans** — UI font (via Google Fonts)
- **React Router** — client-side routing with auth guards
- **Recharts** — performance trend chart
- **react-icons** — UI icons

---

## Notes

- **Auth** — email + password login. Password hashed with argon2. User profile stored in `localStorage` after login.
- **Question selection** — greedy semantic diversity using `all-MiniLM-L6-v2`. Questions with high `times_asked` are deprioritised. Only questions with a valid ideal answer or at least one alternative are eligible.
- **Multi-reference scoring** — questions may have up to 2 alternative answers. The system scores against the best match, preventing penalisation for valid alternative explanations.
- **Coaching feedback** — rule-based narrative derived from numeric scores and detected gaps. Not LLM-generated. Delivery feedback references pace and pauses — not filler words, which Whisper strips.
- **Session rating** — users submit a 1–5 star rating after each session via `POST /ratings/`. Stored in `session_ratings` for satisfaction tracking and future weight calibration.
- **Audio** — browser sends WebM; Whisper handles it directly. File is deleted immediately after transcription.
- **Model warmup** — Whisper, sentence-transformers, and spaCy load at startup via the `lifespan` handler so all responses after the first are fast.

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
    │   ├── semantic_score.py           # sentence-transformers cosine similarity
    │   ├── keyword_score.py            # spaCy lemmatized keyword matching
    │   ├── completeness_score.py       # Structural component + keyword-coverage detection
    │   ├── answer_quality_scorer.py    # Aggregates above three (50/30/20)
    │   ├── confidence_scoring.py       # Grammar/substance, pace, fillers, pauses
    │   ├── feedback_generator.py       # Score-derived coaching narrative
    │   ├── question_generator.py       # Greedy semantic diversity selection
    │   ├── keyword_extractor.py        # KeyBERT extraction (used at seed time)
    │   └── components_generator.py     # Detects expected answer components
    └── scripts/
        ├── scrape_and_seed.py      # Multi-source Q&A scraper + DB seeder
        └── generate_qna_docx.py    # Exports verified Q&A bank to Word document
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
        │       └─ Completeness 20%  (component detection + keyword coverage)
        │
        ├─── Confidence Score (30% of final)
        │       ├─ Grammar/Substance 35%  (original content depth + TTR)
        │       ├─ Filler words      30%  (um, uh, basically, literally…)
        │       ├─ Speaking pace     20%  (WPM — ideal: 120–155)
        │       └─ Pauses            15%  (hesitation gaps > 1s via librosa)
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

## Database Migration & Consistency Fix

### Background

When the behavioral/technical scoring system was implemented, some existing sessions in the database had an inconsistency: `answered > 0` (completed questions) but `total_score = NULL` (missing overall score). This prevented accurate session history display.

### Migration Script

A migration script (`fix_session_scores.py`) was created to fix this inconsistency:

```powershell
cd interview_coach

# Install dependencies if not already installed
python -m pip install sqlalchemy psycopg2-binary python-dotenv

# Run migration from project root
python fix_session_scores.py
```

**What it does:**
1. Finds all sessions with `answered > 0` but `total_score IS NULL`
2. Fetches all responses for each broken session
3. Recalculates `overall_score` using the latest weighting formula:
   - Technical: `answer_quality × 0.70 + confidence × 0.30`
   - Behavioral: `confidence × 0.70 + answer_quality × 0.30`
4. Updates `sessions.total_score` with calculated value
5. Verifies all inconsistencies are fixed

**Results (Executed 2026-08-29):**
- Broken sessions found: **11**
- Sessions fixed: **11/11 (100%)**
- Verification: ✅ **All inconsistencies resolved**

**Sample Fixed Sessions:**
```
Session 102: score=57.19 (Technical)
Session 103: score=71.58 (Behavioral)
Session 106: score=71.65 (Behavioral)
Session 111: score=74.11 (Behavioral)
... and 7 more
```

### Data Consistency Guarantees

After migration:
- ✅ All completed sessions have valid `total_score`
- ✅ `total_score = average(per_question_overall_scores)`
- ✅ `answered = count(responses)` (0–5)
- ✅ Frontend session history displays correctly
- ✅ No NULL scores for sessions with answered > 0

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
| Structural completeness | 20% | Component detection + ideal-answer keyword overlap |

### Confidence Score (0–100)

| Component | Weight | Method |
|---|---|---|
| Grammar / Substance | 35% | Original-content depth, TTR, sentence naturalness |
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

## Frontend Display & Integration

### Session History Card

The frontend displays session summaries in the **Dashboard → Sessions** section:

```
┌─────────────────────────────────────┐
│ Session #256 - SDE Interview        │
├─────────────────────────────────────┤
│ Started: Jan 15, 2025 - 10:30 AM   │
│                                      │
│ Status: ✅ Completed                │
│ Answered: 5/5                       │ ← answered / total_questions
│ Overall Score: 80.24 / 100          │ ← overall_score
│ Interview Type: Behavioral          │
│                                      │
│ Score Breakdown:                    │
│ • Answer Quality: 69.6/100          │
│ • Confidence: 84.8/100              │
│ • Completeness (STAR): 85.0/100     │
│ • Grammar: 75.0/100                 │
│                                      │
│ [View Detailed Feedback] [Retake]   │
└─────────────────────────────────────┘
```

### API Response Format

When the frontend calls `GET /sessions/user/{user_id}/history`, it receives:

```json
[
  {
    "session_id": 256,
    "role": "SDE",
    "completed": true,
    "started_at": "2025-01-15T10:30:00Z",
    "answered": 5,
    "total_questions": 5,
    "overall_score": 80.24,
    "interview_type": "behavioral",
    "scores": {
      "answer_quality_avg": 69.6,
      "semantic_avg": 0,
      "keyword_avg": 0,
      "completeness_avg": 85.0,
      "confidence_avg": 84.8,
      "grammar_avg": 75.0
    }
  }
]
```

### Frontend Integration Notes

1. **Answered Display:** `${answered} / ${total_questions}` (e.g., "3/5")
2. **Score Display:** Use `overall_score` (not database `total_score`)
3. **Interview Type:** Display `interview_type` to show which weighting was applied
4. **Behavioral Questions:**
   - Hide `semantic_avg` and `keyword_avg` (always 0 for behavioral)
   - Display `completeness_avg` as "STAR Completeness" instead of generic "Completeness"
5. **Technical Questions:**
   - Display all component scores normally
   - Use generic "Completeness" label

### Session Calculation Details

**Why scores are recalculated on every read:**
- Ensures fresh calculations reflect latest weights
- Prevents stale data when question type or weighting formulas change
- Single source of truth: Responses table
- No redundancy: No need to maintain both DB scores and calculated scores

---

## Q&A Database

The question bank is built by scraping multiple peer-reviewed sources and stored in PostgreSQL. Each question includes `ideal_answer`, `keywords` (KeyBERT), `expected_components`, `difficulty`, `topic`, `subtopic`, and `experience_level`.

### Sources

| # | Repository / Site | Topics | Questions |
|---|---|---|---|
| 1 | [alexeygrigorev/data-science-interviews](https://github.com/alexeygrigorev/data-science-interviews) | ML, DL, NLP, Clustering, Time Series | ~166 |
| 2 | [youssefHosni/Data-Science-Interview-Questions-Answers](https://github.com/youssefHosni/Data-Science-Interview-Questions-Answers) | ML, Statistics, Probability, Python, DL, SQL | ~100 |
| 3 | [iamtodor/data-science-interview-questions-and-answers](https://github.com/iamtodor/data-science-interview-questions-and-answers) | Regularization, Feature Selection, Metrics | ~32 |
| 4 | [kojino/120-Data-Science-Interview-Questions](https://github.com/kojino/120-Data-Science-Interview-Questions) | Probability, Statistical Inference, EDA, Predictive Modeling, Programming | ~115 |
| 5 | roadmap.sh/questions/data-science | General DS | varies |
| 6 | Expert-curated | SQL, Python, Deep Learning, NLP, MLOps, Feature Engineering | ~32 |

**Total verified questions in DB: ~450+** across 20 topic areas.

### Question Quality Controls

- **Stub rejection** — answers < 40 chars or containing placeholder phrases (`"answer here"`, `"refer to above"`, etc.) are rejected at ingestion and flagged `verified=False` in the DB.
- **Hard session filter** — `question_generator.py` queries only `verified=True AND ideal_answer IS NOT NULL AND code_expected=False`. Unverified questions can never appear in sessions regardless of fallback logic.
- **Deduplication** — MD5 hash of normalised question text prevents duplicates across sources and re-runs.
- **No coding questions in sessions** — implementation/code questions are stored in the DB and appear in the DOCX bank but are excluded from voice sessions (`code_expected=False` filter).

### Running the Scraper

```powershell
# Seed the database (scrapes all sources, deduplicates, extracts keywords)
.\venv_py312\Scripts\python.exe scripts\scrape_and_seed.py

# Export all verified questions to a Word document
pip install python-docx
.\venv_py312\Scripts\python.exe scripts\generate_qna_docx.py
# Output: interview_coach/DS_Interview_QnA_Bank.docx
```

The DOCX includes a cover page, table of contents, and all Q&As organised by Topic → Subtopic, each with difficulty badge, formatted answer, and keywords.

---

## Scoring Robustness

### Anti-Gaming Protections

| Scenario | Completeness | Confidence |
|---|---|---|
| Repeat the question back | ≤ 18 (parroting penalty) | ≤ 32 (substance = 0) |
| Say random technical words | 0–15 (no ideal-keyword overlap) | ≤ 28 (word-count gate) |
| Very short answer (< 8 words) | `word_count × 2` max | ≤ 28 (hard cap) |
| Good substantive answer | 55–100 | 60–90 |

**How each check works:**

- **Parroting detection** (`completeness_score.py`) — `_parroting_ratio()` measures the fraction of the answer's meaningful tokens that overlap with the question's meaningful tokens. If > 70%, the completeness score is capped at 18.
- **Keyword coverage** (`completeness_score.py`) — when no structural components are expected, the score is `overlap(answer ∩ ideal_keywords) / ideal_keywords × length_ratio`. Random words that don't match the ideal answer score near 0.
- **Substance score** (`confidence_scoring.py`) — `_substance_score()` measures original content (words not in the question and not stop words) as 45% of the grammar sub-score. Parroting → substance ≈ 0.
- **Word-count gate** (`confidence_scoring.py`) — answers < 8 words are hard-capped at 28 confidence; 8–15 words are capped linearly up to 50.

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
- **python-docx** — Q&A bank Word document export
- **pwdlib** (argon2) — password hashing

### Frontend
- **React 19** + **Vite**
- **React Router** — client-side routing with auth guards
- **Recharts** — performance trend chart
- **react-icons** — UI icons

---

## Implementation Details & Behavioral Scoring

### Core Scoring Functions

All scoring functions are implemented in `interview_coach/routers/sessions.py`:

#### `calculate_overall_score(scores_dict, interview_type)`
Applies type-specific weighting to individual question scores:
- **Behavioral:** `confidence × 0.70 + answer_quality × 0.30`
- **Technical:** `answer_quality × 0.70 + confidence × 0.30`

#### `calculate_session_score(responses)`
Calculates session-level score as average of all answered questions:
1. Determines interview type from first response
2. Calculates per-question overall score using `calculate_overall_score()`
3. Returns: `(session_score, total_questions=5, answered_count, interview_type)`

**Key feature:** Recalculated on every API call, never cached from DB.

### STAR Component Detection

Implemented in `interview_coach/services/completeness_score.py`:

#### `_detect_star_components(transcript, question_text)`
Pattern-matches 57 trigger phrases across 4 STAR components:
- **57 phrases** across Situation, Task, Action, Result
- **Case-insensitive** substring matching on answer transcript
- **Score calculation:** (components_found / 4) × 100
- **Output:** List of detected components with line numbers

#### Key STAR Trigger Phrases (Sample)
```
Situation:  "when I faced", "in a situation where", "I was assigned", "the challenge was"
Task:       "my role was", "my responsibility", "I was tasked with", "I had to"
Action:     "I decided to", "I approached it by", "I implemented", "I collaborated"
Result:     "the result was", "as a result", "I learned that", "the outcome"
```

### Behavioral Answer Quality Adjustments

In `interview_coach/services/answer_quality_scorer.py`:

```python
# For behavioral questions:
semantic_score = 0          # No ideal answer comparison
keyword_score = 0           # No keyword requirements
completeness_score = 100    # STAR structure score (0-100)
answer_quality = completeness_score  # Uses only STAR for behavioral
```

### Database Schema Changes

**Sessions Table:**
```sql
ALTER TABLE sessions ADD COLUMN question_type VARCHAR(30);
-- Now stores interview type (behavioral/technical) at session creation
-- Used by API to determine weighting formula
```

**Responses Table (No changes needed):**
- `question_type` field already exists (line 65 in models.py)
- `answer_quality_score`, `confidence_score` used for calculation
- All weighting formulas use these two fields

### API Endpoint Modifications

**GET `/sessions/user/{user_id}/history`** (lines 96-148 in sessions.py):
- Queries all sessions for user
- For each session: Fetches responses and **recalculates** overall_score fresh
- Returns: `overall_score` (calculated), `interview_type`, and per-component averages
- Never returns database `total_score` directly

### Migration Script (`fix_session_scores.py`)

Located in project root, fixes data inconsistency:
1. Connects to PostgreSQL using `DATABASE_URL` from `.env`
2. Finds sessions: `answered > 0 AND total_score IS NULL`
3. For each broken session:
   - Fetches all responses
   - Calls `calculate_session_score(responses)` with latest logic
   - Updates `sessions.total_score`
4. Verifies: No broken sessions remain

---

## Notes

- **Auth** — email + password login. Password hashed with argon2. User profile stored in `localStorage` after login. Sign out clears the session.
- **Question selection** — greedy semantic diversity using `all-MiniLM-L6-v2` ensures each session covers different topics. Questions with high `times_asked` are deprioritised so content stays fresh across sessions. Only `verified=True`, non-coding questions with a real `ideal_answer` are eligible.
- **Coaching feedback** — score-derived rule-based narrative. Not LLM-generated. Reads the actual numeric scores and identified gaps to produce specific, actionable paragraphs.
- **Audio** — browser sends WebM; Whisper handles it directly. File is deleted immediately after transcription.
- **Model warmup** — Whisper, sentence-transformers, and spaCy load at startup via the `lifespan` handler, so all responses after the first are fast.
- **Behavioral scoring** — different weighting based on interview type:
  - **Technical** (70% quality, 30% confidence): Emphasises knowledge and accuracy
  - **Behavioral** (70% confidence, 30% quality): Emphasises communication and STAR storytelling
  - Type detected from question metadata; weights applied at session-level averaging
  - Session scores always recalculated fresh from Responses table, never cached
- **STAR framework** — Behavioral answers evaluated on 4 components: Situation, Task, Action, Result. 57 trigger phrases detect each component. Missing STAR components receive lower completeness scores.
- **Multi-reference scoring** — questions may have up to 2 alternative answers. System scores against the best match (highest semantic similarity), preventing penalisation for valid alternatives.
- **Data consistency** — migration script fixes incomplete sessions with missing scores. All sessions with `answered > 0` guarantee valid `total_score` after migration.

---

## Troubleshooting

### Migration Script Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'sqlalchemy'` | Dependencies not installed | Run `pip install sqlalchemy psycopg2-binary python-dotenv` |
| `DATABASE_URL is None` | `.env` file not found | Copy `interview_coach/.env` to project root: `cp interview_coach/.env .env` |
| Script runs but no output | Encoding issue on Windows | Python script handles encoding automatically; if still silent, check `.env` file exists |
| `No broken sessions found` | Database already consistent | This is success! All sessions have valid scores. |
| `Still X sessions with missing scores` | Migration failed partially | Check logs for specific session errors; may indicate corrupt response data |

### Session History Display Issues

| Symptom | Check |
|---------|-------|
| Sessions showing `overall_score: NULL` | Run migration script; check `.env` DATABASE_URL |
| Frontend shows "Answered: 0/5" for completed session | Verify Responses created for each question; check `sessions.answered` matches response count |
| STAR components not displayed for behavioral | Verify `interview_type = "behavioral"` in API response; frontend should map to STAR display |
| Inconsistent scores between sessions | All sessions recalculated fresh; scores will differ by weighting differences (technical vs behavioral) |

---

## Key Files & Changes Summary

### Files Modified

| File | Lines | Changes | Purpose |
|------|-------|---------|---------|
| `interview_coach/routers/sessions.py` | 26-88 | Added `calculate_overall_score()` and `calculate_session_score()` | Type-aware weighting & session averaging |
| `interview_coach/routers/sessions.py` | 96-148 | Updated `get_user_sessions()` endpoint | Fresh score calculation, returns `overall_score` and `interview_type` |
| `interview_coach/services/completeness_score.py` | 44-68 | Added `STAR_PATTERNS` dictionary (57 phrases) | Behavioral question component detection |
| `interview_coach/services/completeness_score.py` | 125-143 | Added `_detect_star_components()` function | Pattern-matching for STAR components |
| `interview_coach/services/completeness_score.py` | 162-287 | Updated `compute_completeness_score()` logic | Branch for behavioral vs technical scoring |
| `interview_coach/services/answer_quality_scorer.py` | 124-130 | Pass `question_type` to completeness scorer | Enable STAR detection |

### Files Created

| File | Purpose | Contents |
|------|---------|----------|
| `fix_session_scores.py` | Migration script | Find & fix NULL `total_score` values, verify results |
| `.env` | Environment configuration | Copied from `interview_coach/.env` to enable migration script |
| `SESSION_SCORING_EXPLAINED.md` | Documentation | Complete visual guide to session scoring architecture |

### Database Tables (No migrations needed)

| Table | Field | Already Exists? | Usage |
|-------|-------|-----------------|-------|
| `Sessions` | `question_type` | ❓ May need manual add | Stores interview type for quick lookup |
| `Sessions` | `total_score` | ✅ Yes | Populated by migration script |
| `Sessions` | `answered` | ✅ Yes | Incremented as responses added |
| `Responses` | `question_type` | ✅ Yes | Source of truth for type-aware calculation |
| `Responses` | `answer_quality_score` | ✅ Yes | Used in weighting formula |
| `Responses` | `confidence_score` | ✅ Yes | Used in weighting formula |

### How to Find Implementation Details

**Behavioral Scoring Logic:**
- `interview_coach/routers/sessions.py` lines 26-48 → `calculate_overall_score()`
- `interview_coach/services/completeness_score.py` lines 44-68 → STAR patterns
- `interview_coach/services/completeness_score.py` lines 125-143 → STAR detection

**Session Average Calculation:**
- `interview_coach/routers/sessions.py` lines 51-88 → `calculate_session_score()`
- `interview_coach/routers/sessions.py` lines 96-148 → `get_user_sessions()` endpoint

**Data Consistency Fix:**
- `fix_session_scores.py` lines 50-74 → Migration logic
- `fix_session_scores.py` lines 87-133 → Verification logic

---

## References & Additional Documentation

- **SCORING_FLOW_DIAGRAMS.md** — Visual flowcharts of session calculation and database architecture
- **SESSION_SCORING_EXPLAINED.md** — Complete breakdown of scoring with examples
- **IMPLEMENTATION_SUMMARY.md** — Comprehensive feature overview (from prior checkpoint)
