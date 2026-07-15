import spacy

# Load spaCy model with error handling
try:
    nlp = spacy.load("en_core_web_sm")
    print("✓ spaCy model loaded successfully")
except OSError:
    print("❌ spaCy model not found! Installing...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=False)
    nlp = spacy.load("en_core_web_sm")


def compute_keyword_score(transcript: str, keywords_str: str) -> tuple[float, list[str]]:
    try:
        if not keywords_str or not keywords_str.strip():
            return 0.0, []

        keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]

        if not keywords:
            return 0.0, []

        # Lemmatize the transcript
        doc = nlp(transcript.lower())
        lemmatized_text = " ".join(token.lemma_ for token in doc)
        print(f"📝 Lemmatized transcript: {lemmatized_text[:100]}...")

        matched = []
        missed = []

        for kw in keywords:
            lemmatized_kw = " ".join(token.lemma_ for token in nlp(kw))
            if lemmatized_kw in lemmatized_text:
                matched.append(kw)
            else:
                missed.append(kw)

        score = round((len(matched) / len(keywords)) * 100, 2)
        print(f"🔑 Keyword score: {score} ({len(matched)}/{len(keywords)} matched)")

        return score, missed
    except Exception as e:
        print(f"❌ Keyword scoring error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    transcript = "machine is trained on the labeled data"
    keywords_str = "machine,label,data,train"

    score, missed = compute_keyword_score(transcript, keywords_str)

    print(f"Keyword Score : {score}")
    print(f"Missed        : {missed}")