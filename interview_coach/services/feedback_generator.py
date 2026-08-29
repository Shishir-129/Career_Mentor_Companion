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
    if 120 <= d["speaking_speed"] <= 155:
        strengths.append("Excellent speaking pace (120-155 WPM).")
    elif 100 <= d["speaking_speed"] < 120 or 155 < d["speaking_speed"] <= 175:
        strengths.append("Comfortable speaking pace — easy for an interviewer to follow.")
    return strengths or ["Keep practising to build confidence and depth."]


def _derive_improvements(d: dict, question_type: str = "technical") -> list[str]:
    # coaching_tips are already the human-readable form of components_missing
    # (e.g. "Try opening with a clear definition.") — don't add components_missing
    # separately as it would repeat the same information in a different format.
    improvements = list(d["coaching_tips"])
    # For behavioral questions, skip keyword suggestions — STAR structure feedback is sufficient
    if d["missed_keywords"] and question_type.lower() != "behavioral":
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
    question_type: str = "technical",
) -> str:
    is_behavioral = question_type.lower() == "behavioral"

    # ── Opening: overall answer quality ──────────────────────────────────────
    if is_behavioral:
        if answer_quality_score >= 80:
            opening = "Strong answer — you told a clear, well-structured story."
        elif answer_quality_score >= 65:
            opening = "Good response. Your story covered most of the key elements."
        elif answer_quality_score >= 45:
            opening = "Your answer has potential but needs a clearer story structure (Situation → Task → Action → Result)."
        else:
            opening = "Focus on structuring your answer: describe the Situation, your Task, the Action you took, and the Result."
    else:
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
    if is_behavioral:
        if completeness_score >= 75:
            middle = "Your answer had a clear structure — the interviewer could follow your story easily."
        elif completeness_score >= 50:
            middle = "Good attempt, but try to be more explicit about the outcome or result of your action."
        else:
            middle = "Structure your answer using the STAR method: Situation, Task, Action, Result."
    else:
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
        closing = "Decent delivery. Aim for a steady pace and reduce hesitation pauses to come across more polished."
    else:
        closing = "Focus on your delivery: target 120-155 WPM and try to minimise long pauses between thoughts."

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
    question_type: str = "technical",
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
        },
        question_type=question_type,
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
        question_type=question_type,
    )
    return {
        "answer_quality_score": answer_quality_score,
        "confidence_score": confidence_score,
        "narrative_feedback": narrative,
        "strengths": strengths,
        "improvements": improvements,
    }
