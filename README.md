# Interview Coach API

An AI-powered interview coaching system with real-time audio processing, transcription, and intelligent feedback generation.

---

## ⚠️ CRITICAL: Python 3.12.10 REQUIRED

This project **MUST** use **Python 3.12.10**. Older versions (Python 3.14) cause PyTorch crashes at the C++ level.

## Requirements

- **Python 3.12.10** (NOT 3.13, NOT 3.14, NOT 3.10)
- PostgreSQL database (Neon or local)
- Node.js 18+ (for frontend)
- ~2GB disk space for ML models

---

## Installation

### 1. Install Python 3.12.10

**Windows:**
```powershell
# Using winget
winget install Python.Python.3.12

# Verify installation
python3.12 --version  # Should output: Python 3.12.10
```

**macOS:**
```bash
# Using Homebrew
brew install python@3.12

# Verify
python3.12 --version
```

### 2. Clone and navigate to project

```bash
git clone <your-repo-url>
cd interview_coach
```

### 3. Create and activate virtual environment

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