import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=False)
    nlp = spacy.load("en_core_web_sm")


def compute_keyword_score(transcript: str, keywords_str: str) -> tuple[float, list[str]]:
    if not keywords_str or not keywords_str.strip():
        return 0.0, []

    keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]
    if not keywords:
        return 0.0, []

    doc = nlp(transcript.lower())
    lemmatized_text = " ".join(token.lemma_ for token in doc)

    matched, missed = [], []
    for kw in keywords:
        lemmatized_kw = " ".join(token.lemma_ for token in nlp(kw))
        (matched if lemmatized_kw in lemmatized_text else missed).append(kw)

    score = round((len(matched) / len(keywords)) * 100, 2)
    return score, missed