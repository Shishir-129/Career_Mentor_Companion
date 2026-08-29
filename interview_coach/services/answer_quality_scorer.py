import json
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
    question_text: str = "",
    alternatives: list[str] | None = None,
    alternative_answer_keywords: dict | None = None,
    alternative_answer_components: dict | None = None,
) -> dict:
    """
    Aggregates three sub-scores into a single Answer Quality Score.

    Strategy:
    1. Semantic scoring finds the BEST matching reference answer (ideal or alternative).
    2. Keyword + completeness scoring use THAT answer's keywords/components — not always
       the ideal's — so the user is graded fairly against the style they actually matched.

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
        coaching_tips         — list[str]
        matched_answer_type   — "ideal" or "alternative_N"
    """
    try:
        # ── Step 1: Semantic score — also tells us which reference answer matched best ─
        sem = compute_semantic_score(user_answer, ideal_answer, alternatives=alternatives)
        semantic_score = sem["score"]
        best_index     = sem["best_index"]
        best_answer    = sem["best_answer"]

        print(f"Best match: {'ideal' if best_index == 0 else f'alternative_{best_index - 1}'} (score={semantic_score}%)")

        # ── Step 2: Pick keywords/components for the best matching answer ─────────────
        if best_index == 0:
            # Matched the ideal answer — use its stored keywords and components
            active_keywords_str    = keywords_str
            active_components_json = expected_components_json
        else:
            # Matched an alternative — use that alternative's pre-stored metadata
            alt_key = f"alternative_{best_index - 1}"

            alt_kw_list = []
            if alternative_answer_keywords and isinstance(alternative_answer_keywords, dict):
                alt_kw_list = alternative_answer_keywords.get(alt_key, [])
            # Fall back to ideal's keywords if alternative has none
            active_keywords_str = ", ".join(alt_kw_list) if alt_kw_list else keywords_str

            alt_comp_list = []
            if alternative_answer_components and isinstance(alternative_answer_components, dict):
                alt_comp_list = alternative_answer_components.get(alt_key, [])
            # Fall back to ideal's components if alternative has none
            active_components_json = json.dumps(alt_comp_list) if alt_comp_list else expected_components_json

        # ── Step 3: Keyword score against the best answer's keywords ──────────────────
        if active_keywords_str and active_keywords_str.strip():
            keyword_score, missed_keywords = compute_keyword_score(user_answer, active_keywords_str)
            w_semantic = WEIGHTS["semantic"]
            w_keyword  = WEIGHTS["keyword"]
        else:
            # No keywords defined (e.g. behavioral/theoretical question) —
            # For questions with no keywords: 80% semantic + 20% completeness
            keyword_score   = 0.0
            missed_keywords = []
            w_semantic = 0.80  # 80% semantic
            w_keyword  = 0.0   # 0% keyword

        # ── Step 4: Completeness score against the best answer ────────────────────────
        comp = compute_completeness_score(
            user_answer=user_answer,
            expected_components_json=active_components_json,
            ideal_answer=best_answer,   # use best matched answer, not always the ideal
            question_text=question_text,
            alternatives=None,          # already resolved the best match above
        )
        completeness_score = comp["completeness_score"]

        # ── Step 5: Weighted aggregate ────────────────────────────────────────────────
        answer_quality_score = round(
            semantic_score     * w_semantic           +
            keyword_score      * w_keyword            +
            completeness_score * 0.20,  # 20% completeness
            2,
        )

        return {
            "answer_quality_score": answer_quality_score,
            "quality_label":        get_quality_label(answer_quality_score),
            "semantic_score":       semantic_score,
            "keyword_score":        round(keyword_score, 2),
            "completeness_score":   completeness_score,
            "missed_keywords":      missed_keywords,
            "components_missing":   comp["components_missing"],
            "coaching_tips":        comp["coaching_tips"],
            "matched_answer_type":  "ideal" if best_index == 0 else f"alternative_{best_index - 1}",
        }
    except Exception as e:
        import logging, traceback
        logging.getLogger(__name__).error("Answer quality scoring error: %s", e)
        traceback.print_exc()
        return {
            "answer_quality_score": 50.0,
            "quality_label": "Average",
            "semantic_score": 0.0,
            "keyword_score": 0.0,
            "completeness_score": 0.0,
            "missed_keywords": [],
            "components_missing": [],
            "coaching_tips": ["Please check your answer and try again"],
            "matched_answer_type": "ideal",
        }
