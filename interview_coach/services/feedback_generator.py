from __future__ import annotations


def _get_label(score: float) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 45:
        return "Average"
    return "Poor"


def _derive_strengths(d: dict) -> list[str]:
    strengths = []
    if d["semantic_score"] >= 65:
        strengths.append("Good conceptual understanding of the topic.")
    if d["keyword_score"] >= 65:
        strengths.append("Strong use of technical vocabulary.")
    if d["completeness_score"] >= 65:
        strengths.append("Answer covered the key structural components.")
    if d["grammar_score"] >= 65:
        strengths.append("Clear and articulate language.")
    if d["filler_count"] <= 1:
        strengths.append("Confident delivery with minimal filler words.")
    if 120 <= d["speaking_speed"] <= 155:
        strengths.append("Excellent speaking pace (120-155 WPM).")
    return strengths or ["Keep practising to build confidence and depth."]


def _derive_improvements(d: dict) -> list[str]:
    # coaching_tips are already the human-readable form of components_missing
    # (e.g. "Try opening with a clear definition.") — don't add components_missing
    # separately as it would repeat the same information in a different format.
    improvements = list(d["coaching_tips"])
    if d["missed_keywords"]:
        kws = ", ".join(d["missed_keywords"])
        improvements.append(f"Include these technical terms in your answer: {kws}.")
    return improvements


def _build_narrative(
    answer_quality_score: float,
    confidence_score: float,
    semantic_score: float,
    keyword_score: float,
    completeness_score: float,
    strengths: list[str],
    improvements: list[str],
    word_count: int = 0,
) -> str:
    # ── Opening: overall answer quality ──────────────────────────────────────
    if answer_quality_score >= 80:
        opening = "Strong answer — you demonstrated a solid, well-rounded understanding of the topic."
    elif answer_quality_score >= 65:
        opening = "Good response overall. You covered the core concept effectively."
    elif answer_quality_score >= 45:
        opening = "Your answer shows a basic understanding, but needs more depth and structure to stand out."
    else:
        opening = "This answer needs significant work. Focus on explaining concepts clearly with supporting examples."

    # Flag if the answer was too brief
    if 0 < word_count < 25:
        opening += " Your answer was quite brief — interviewers generally expect more elaboration."

    # ── Middle: diagnostic observation specific to the score profile ──────────
    if semantic_score >= 75 and keyword_score >= 65:
        middle = "You showed both conceptual clarity and good use of technical terms."
    elif semantic_score >= 65 and keyword_score < 50:
        middle = "You understood the concept well, but missed several key technical terms that interviewers specifically listen for."
    elif semantic_score < 50 and keyword_score >= 65:
        middle = "You used the right terminology, but the core explanation drifted from what was being asked."
    elif completeness_score < 50:
        middle = "The answer touched on the topic but was missing important structural elements — a definition or a concrete example would strengthen it considerably."
    elif strengths:
        middle = strengths[0]
    else:
        middle = ""

    # ── Improvement: most actionable next step ────────────────────────────────
    if improvements:
        improve = f"To improve: {improvements[0].rstrip('.')}."
    else:
        improve = "Keep practising — consistency is the fastest path to improvement."

    # ── Closing: delivery ─────────────────────────────────────────────────────
    if confidence_score >= 75:
        closing = "Your delivery was confident and clear — that composure will serve you well in real interviews."
    elif confidence_score >= 55:
        closing = "Decent delivery. Work on reducing filler words to come across more polished."
    else:
        closing = "Focus on your delivery: aim for a steady 120-155 WPM pace and cut filler words like 'um' and 'uh'."

    parts = [opening]
    if middle:
        parts.append(middle)
    parts.append(improve)
    parts.append(closing)
    return " ".join(parts)


def generate_feedback(
    answer_quality_score: float,
    quality_label: str,
    semantic_score: float,
    keyword_score: float,
    completeness_score: float,
    missed_keywords: list[str],
    components_missing: list[str],
    coaching_tips: list[str],
    confidence_score: float,
    grammar_score: float,
    speaking_speed: float,
    filler_count: int,
    pause_count: int,
    transcript: str = "",
) -> dict:
    strengths = _derive_strengths(
        {
            "semantic_score": semantic_score,
            "keyword_score": keyword_score,
            "completeness_score": completeness_score,
            "grammar_score": grammar_score,
            "filler_count": filler_count,
            "speaking_speed": speaking_speed,
        }
    )
    improvements = _derive_improvements(
        {
            "coaching_tips":   coaching_tips,
            "missed_keywords": missed_keywords,
        }
    )

    word_count = len(transcript.split()) if transcript.strip() else 0

    narrative = _build_narrative(
        answer_quality_score=answer_quality_score,
        confidence_score=confidence_score,
        semantic_score=semantic_score,
        keyword_score=keyword_score,
        completeness_score=completeness_score,
        strengths=strengths,
        word_count=word_count,
        improvements=improvements,
    )
    return {
        "answer_quality_score": answer_quality_score,
        "confidence_score": confidence_score,
        "narrative_feedback": narrative,
        "strengths": strengths,
        "improvements": improvements,
    }
