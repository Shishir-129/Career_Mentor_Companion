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

### Overall Session Score

```
OVERALL = Answer Quality × 0.70 + Confidence × 0.30
```

Content quality is weighted more heavily than delivery, reflecting how technical interviewers prioritise domain knowledge.

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

## Notes

- **Auth** — email + password login. Password hashed with argon2. User profile stored in `localStorage` after login. Sign out clears the session.
- **Question selection** — greedy semantic diversity using `all-MiniLM-L6-v2` ensures each session covers different topics. Questions with high `times_asked` are deprioritised so content stays fresh across sessions. Only `verified=True`, non-coding questions with a real `ideal_answer` are eligible.
- **Coaching feedback** — score-derived rule-based narrative. Not LLM-generated. Reads the actual numeric scores and identified gaps to produce specific, actionable paragraphs.
- **Audio** — browser sends WebM; Whisper handles it directly. File is deleted immediately after transcription.
- **Model warmup** — Whisper, sentence-transformers, and spaCy load at startup via the `lifespan` handler, so all responses after the first are fast.
