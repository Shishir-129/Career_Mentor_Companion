import spacy

nlp = spacy.load("en_core_web_sm")

def compute_keyword_score(transcript: str, keywords_str: str) -> tuple[float, list[str]]:
    if not keywords_str or not keywords_str.strip():
        return 0.0, []

    keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]

    if not keywords:
        return 0.0, []

    #lemmatizing the scripts
    doc = nlp(transcript.lower())
    lemmatized_text = " ".join(token.lemma_ for token in doc)
    print(lemmatized_text)

    matched = []
    missed = []

    for kw in keywords:
        lemmatized_kw = " ".join(token.lemma_ for token in nlp(kw))
        if lemmatized_kw in lemmatized_text:
            matched.append(kw)
        else:
            missed.append(kw)

    

    score = round((len(matched) / len(keywords)) * 100, 2)

    return score, missed

if __name__ == "__main__":
    transcript = "machine is trained on the labeled data"
    keywords_str = "machine,label,data,train"

    score, missed = compute_keyword_score(transcript, keywords_str)

    print(f"Keyword Score : {score}")
    print(f"Missed        : {missed}")