from sentence_transformers import SentenceTransformer, util

# Load model once at module level — cached in RAM for reuse
_model = SentenceTransformer("all-MiniLM-L6-v2")


def get_model():
    """Return the cached sentence-transformers model."""
    return _model


# Score interpretation thresholds
EXCELLENT_THRESHOLD = 85
GOOD_THRESHOLD = 65
AVERAGE_THRESHOLD = 45


def get_semantic_label(score: float) -> str:
    if score >= EXCELLENT_THRESHOLD:
        return "Excellent"
    elif score >= GOOD_THRESHOLD:
        return "Good"
    elif score >= AVERAGE_THRESHOLD:
        return "Average"
    else:
        return "Poor"


def compute_semantic_score(
    user_answer: str,
    ideal_answer: str,
    alternatives: list[str] | None = None,
) -> dict:
    """
    Compute semantic similarity between user's answer and the ideal answer.
    If alternatives are provided, picks the best score across all candidates
    and returns which candidate won.

    Returns:
        score        — float between 0 and 100
        label        — interpretation string (Excellent / Good / Average / Poor)
        best_index   — int: 0 = ideal, 1 = alternative_0, 2 = alternative_1 ...
        best_answer  — str: the reference answer text that matched best
    """
    if not user_answer or not user_answer.strip():
        return {"score": 0.0, "label": "Poor", "best_index": 0, "best_answer": ideal_answer}

    if not ideal_answer or not ideal_answer.strip():
        return {"score": 0.0, "label": "Poor", "best_index": 0, "best_answer": ""}

    # Build list of all reference answers to compare against
    candidates = [ideal_answer] + [a for a in (alternatives or []) if a and a.strip()]

    user_embedding = _model.encode(user_answer, convert_to_tensor=True)
    candidate_embeddings = _model.encode(candidates, convert_to_tensor=True)

    similarities = util.cos_sim(user_embedding, candidate_embeddings)[0]
    similarities_list = [float(s.item()) for s in similarities]

    best_index = int(similarities_list.index(max(similarities_list)))
    best_similarity = similarities_list[best_index]
    score = round(max(0.0, best_similarity) * 100, 2)

    return {
        "score":       score,
        "label":       get_semantic_label(score),
        "best_index":  best_index,
        "best_answer": candidates[best_index],
    }
