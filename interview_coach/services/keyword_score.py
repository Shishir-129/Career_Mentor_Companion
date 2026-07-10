import spacy
nlp = spacy.load("en_core_web_sm")


def compute_keyword_score(transcript: str, keywords_str: str) -> tuple[float, list[str]]:

    if not keywords_str or not keywords_str.strip():
        return 0.0, []

    keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]

    if not keywords:
        return 0.0, []

    transcript_lower = transcript.lower()
    doc = nlp(transcript_lower)
    lemmatized_text = " ".join([token.lemma_ for token in doc])

    matched = []
    missed  = []

    for keyword in keywords:
        kw_doc = nlp(keyword)
        lemmatized_kw = " ".join([token.lemma_ for token in kw_doc])

        if (lemmatized_kw in lemmatized_text or
            keyword in lemmatized_text or
            keyword in transcript_lower):
            matched.append(keyword)
        else:
            missed.append(keyword)

    score = (len(matched) / len(keywords)) * 100

    return round(score, 2), missed


if __name__ == "__main__":
    transcript   = "supervised learning trains on labeled data and training data to predict output"
    keywords_str = "supervised learning, labeled data, training data, predict"

    score, missed = compute_keyword_score(transcript, keywords_str)

    print(f"Keyword Score : {score}")
    print(f"Missed        : {missed}")