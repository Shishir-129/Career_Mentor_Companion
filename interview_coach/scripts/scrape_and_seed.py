import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import requests
from bs4 import BeautifulSoup
from database.connection import SessionLocal
from crud.questions import create_question
from schemas.question import QuestionCreate
from services.keyword_extractor import extract_keywords   # ← ADD THIS

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
    return None, text

def scrape():
    url = "https://alexeygrigorev.com/data-science-interviews/theory.html"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    questions = []
    current_topic = None
    # Include ul and pre so bullet points and code blocks are captured
    all_tags = soup.find_all(["h2", "p", "ul", "pre"])

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
                answer_parts = []
                j = i + 1
                while j < len(all_tags):
                    next_tag = all_tags[j]

                    if next_tag.name == "h2":
                        break

                    if next_tag.name == "p":
                        next_text = next_tag.get_text(strip=True)
                        if get_difficulty(next_text)[0] is not None:
                            break
                        if next_text:
                            answer_parts.append(next_text)

                    elif next_tag.name == "ul":
                        items = [
                            f"- {li.get_text(strip=True)}"
                            for li in next_tag.find_all("li")
                            if li.get_text(strip=True)
                        ]
                        if items:
                            answer_parts.append("\n".join(items))

                    elif next_tag.name == "pre":
                        code_text = next_tag.get_text(strip=True)
                        if code_text:
                            answer_parts.append(f"```\n{code_text}\n```")

                    j += 1

                ideal_answer_text = "\n\n".join(answer_parts)

                questions.append(QuestionCreate(
                    role="Data Scientist",
                    topic=current_topic,
                    difficulty=difficulty,
                    question_type="theory",
                    question_text=question_text,
                    ideal_answer=ideal_answer_text,
                    keywords=", ".join(extract_keywords(ideal_answer_text)),
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