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


def compute_semantic_score(user_answer: str, ideal_answer: str) -> dict:
    """
    Compute semantic similarity between user's answer and the ideal answer.

    Returns:
        score     — float between 0 and 100
        label     — interpretation string (Excellent / Good / Average / Poor)
    """
    if not user_answer or not user_answer.strip():
        return {"score": 0.0, "label": "Poor"}

    if not ideal_answer or not ideal_answer.strip():
        return {"score": 0.0, "label": "Poor"}

    user_embedding = _model.encode(user_answer, convert_to_tensor=True)
    ideal_embedding = _model.encode(ideal_answer, convert_to_tensor=True)

    # cos_sim returns a tensor; .item() converts to Python float
    similarity = util.cos_sim(user_embedding, ideal_embedding).item()

    # Cosine similarity range is [-1, 1]; clamp to [0, 1] then scale to 100
    score = round(max(0.0, similarity) * 100, 2)

    return {"score": score, "label": get_semantic_label(score)}
