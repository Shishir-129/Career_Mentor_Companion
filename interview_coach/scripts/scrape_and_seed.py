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

def get_difficulty(text):
    for emoji, level in DIFFICULTY_MAP.items():
        if emoji in text:
            return level, text.replace(emoji, "").strip()
    return None, text  # not a question line

def scrape():
    url = "https://alexeygrigorev.com/data-science-interviews/theory"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    questions = []
    current_topic = None
    all_tags = soup.find_all(["h2", "p"])

    i = 0
    while i < len(all_tags):
        tag = all_tags[i]

        if tag.name == "h2":
            current_topic = tag.get_text(strip=True)
            i += 1
            continue

        if tag.name == "p":
            text = tag.get_text(strip=True)
            difficulty, question_text = get_difficulty(text)

            if difficulty and question_text and current_topic:
                # Collect answer from following <p> tags
                answer_parts = []
                j = i + 1
                while j < len(all_tags):
                    next_tag = all_tags[j]
                    next_text = next_tag.get_text(strip=True)
                    # Stop when we hit the next question or a new section
                    if next_tag.name == "h2" or get_difficulty(next_text)[0] is not None:
                        break
                    if next_tag.name == "p" and next_text:
                        answer_parts.append(next_text)
                    j += 1

                questions.append(QuestionCreate(
                    role="Data Scientist",
                    topic=current_topic,
                    difficulty=difficulty,
                    question_type="theory",
                    question_text=question_text,
                    ideal_answer=" ".join(answer_parts[:3]),
                    keywords="",
                    verified=True,
                ))
        i += 1

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