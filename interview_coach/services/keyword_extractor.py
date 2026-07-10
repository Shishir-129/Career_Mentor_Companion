from keybert import KeyBERT

kw_model = KeyBERT()

def extract_keywords(text: str, top_n: int = 8) -> list[str]:
    if not text or not text.strip():
        return []

    keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=top_n,
        use_maxsum=True,   # ← removes redundant similar keywords
        nr_candidates=20,
    )

    return [kw for kw, score in keywords]