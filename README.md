# Interview Coach API

A REST API built with FastAPI and PostgreSQL (Neon).

---

## Requirements

- Python 3.10+
- PostgreSQL database (Neon or local)

---

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd interview_coach
```

### 2. Create and activate a virtual environment

```bash
# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:password@host/dbname
```

Replace with your actual Neon (or local PostgreSQL) connection string.

---

## Requirements.txt

```
fastapi
uvicorn
sqlalchemy
psycopg2-binary
pydantic[email]
pwdlib[argon2]
python-dotenv
```

Generate it with:

```bash
pip freeze > requirements.txt
```

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