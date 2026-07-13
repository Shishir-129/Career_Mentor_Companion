from services.semantic_score import compute_semantic_score
from services.keyword_score import compute_keyword_score
from services.completeness_score import compute_completeness_score

# ─── Weights — must sum to 1.0 ────────────────────────────────────────────────
# Semantic     50%: conceptual understanding — most important quality signal
# Keyword      30%: technical vocabulary depth
# Completeness 20%: structural coverage of the answer
WEIGHTS = {
    "semantic":     0.50,
    "keyword":      0.30,
    "completeness": 0.20,
}

# Score label thresholds (shared with semantic scorer for consistency)
EXCELLENT_THRESHOLD = 85
GOOD_THRESHOLD      = 65
AVERAGE_THRESHOLD   = 45


def get_quality_label(score: float) -> str:
    if score >= EXCELLENT_THRESHOLD: return "Excellent"
    if score >= GOOD_THRESHOLD:      return "Good"
    if score >= AVERAGE_THRESHOLD:   return "Average"
    return "Poor"


def compute_answer_quality_score(
    user_answer: str,
    ideal_answer: str,
    keywords_str: str | None,
    expected_components_json: str | None,
) -> dict:
    """
    Aggregates three sub-scores into a single Answer Quality Score.

    answer_quality_score = (semantic × 0.50)
                         + (keyword  × 0.30)
                         + (completeness × 0.20)

    Returns:
        answer_quality_score  — float 0–100
        quality_label         — Excellent / Good / Average / Poor
        semantic_score        — float 0–100
        keyword_score         — float 0–100
        completeness_score    — float 0–100
        missed_keywords       — list[str]
        components_missing    — list[str]
        coaching_tips         — list[str]  (from completeness scorer)
    """
    # ── Semantic score ────────────────────────────────────────────────────────
    sem = compute_semantic_score(user_answer, ideal_answer)
    semantic_score = sem["score"]

    # ── Keyword score ─────────────────────────────────────────────────────────
    if keywords_str and keywords_str.strip():
        keyword_score, missed_keywords = compute_keyword_score(user_answer, keywords_str)
    else:
        keyword_score  = 0.0
        missed_keywords = []

    # ── Completeness score ────────────────────────────────────────────────────
    comp = compute_completeness_score(
        user_answer=user_answer,
        expected_components_json=expected_components_json,
        ideal_answer=ideal_answer,
    )
    completeness_score = comp["completeness_score"]

    # ── Weighted aggregate ────────────────────────────────────────────────────
    answer_quality_score = round(
        semantic_score     * WEIGHTS["semantic"]     +
        keyword_score      * WEIGHTS["keyword"]      +
        completeness_score * WEIGHTS["completeness"],
        2,
    )

    return {
        "answer_quality_score": answer_quality_score,
        "quality_label":        get_quality_label(answer_quality_score),
        "semantic_score":       semantic_score,
        "keyword_score":        round(keyword_score, 2),
        "completeness_score":   completeness_score,
        "missed_keywords":      missed_keywords,+
        "components_missing":   comp["components_missing"],
        "coaching_tips":        comp["coaching_tips"],
    }
