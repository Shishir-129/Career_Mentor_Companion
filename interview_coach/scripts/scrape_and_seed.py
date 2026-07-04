import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import requests
from bs4 import BeautifulSoup
from database.connection import SessionLocal
from crud.questions import create_question
from schemas.question import QuestionCreate

DIFFICULTY_MAP = {
    "👶": "easy",
    "⭐️": "medium",
    "‍⭐️": "medium",
    "🚀": "expert",
}

def scrape():
    url = "https://alexeygrigorev.com/data-science-interviews/theory"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    questions = []
    current_topic = None

    for tag in soup.find_all(["h2", "h4", "p"]):
        if tag.name == "h2":
            current_topic = tag.get_text(strip=True)

        elif tag.name == "h4":
            text = tag.get_text(strip=True)
            difficulty = "medium"
            for emoji, level in DIFFICULTY_MAP.items():
                if emoji in text:
                    difficulty = level
                    text = text.replace(emoji, "").strip()
                    break

            answer_parts = []
            for sib in tag.find_next_siblings():
                if sib.name in ["h4", "h2"]:
                    break
                if sib.name == "p":
                    answer_parts.append(sib.get_text(strip=True))

            if text:
                questions.append(QuestionCreate(
                    role="Data Scientist",   # general — Gemini maps to specific roles
                    topic=current_topic,
                    difficulty=difficulty,
                    question_type="theory",
                    question_text=text,
                    ideal_answer=" ".join(answer_parts[:3]),
                    keywords="",
                    verified=True,
                ))
    return questions

def seed():
    db = SessionLocal()
    questions = scrape()
    for q in questions:
        create_question(db, q)
    db.close()
    print(f"Seeded {len(questions)} questions.")

if __name__ == "__main__":
    seed()