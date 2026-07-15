from __future__ import annotations
from transformers import pipeline

# ─── Model config ──────────────────────────────────────────────────────────────
# flan-t5-base : ~250MB, 2–5s on CPU  ← default (practical for local deployment)
# flan-t5-large: ~780MB, 15–25s on CPU ← swap here for richer prose
_MODEL_NAME = "google/flan-t5-base"

# Lazy-loaded — model is NOT loaded at import time to avoid slowing app startup.
# It loads on the first feedback request and stays in memory after that.
_generator = None


def _get_generator():
    global _generator
    if _generator is None:
        _generator = pipeline(
            "text2text-generation",
            model=_MODEL_NAME,
            device=-1,          # CPU; change to 0 if GPU is available
        )
    return _generator


# ─── Final score weights ───────────────────────────────────────────────────────
# Content quality matters more than delivery in a technical interview
_FINAL_WEIGHTS = {"answer_quality": 0.70, "confidence": 0.30}


def _get_label(score: float) -> str:
    if score >= 85: return "Excellent"
    if score >= 65: return "Good"
    if score >= 45: return "Average"
    return "Poor"


# ─── Prompt builder ────────────────────────────────────────────────────────────
def _build_prompt(d: dict) -> str:
    missed = ", ".join(d["missed_keywords"]) or "none"
    missing = ", ".join(d["components_missing"]) or "none"
    
    # Build context about what went well and what needs improvement
    strengths_text = ", ".join(d["strengths"]) if d["strengths"] else "Continue practicing to build confidence."
    gaps_text = ", ".join(d["improvements"]) if d["improvements"] else "Overall, good work."

    return (
        f"You are an expert technical interview coach providing constructive feedback.\n\n"
        f"CANDIDATE'S RESPONSE:\n\"{d['transcript']}\"\n\n"
        f"PERFORMANCE ANALYSIS:\n"
        f"- Answer Quality Score: {d['answer_quality_score']:.0f}/100 "
        f"(Conceptual: {d['semantic_score']:.0f}, Technical Terms: {d['keyword_score']:.0f}, Completeness: {d['completeness_score']:.0f})\n"
        f"- Delivery Score: {d['confidence_score']:.0f}/100 "
        f"(Grammar: {d['grammar_score']:.0f}, Pace: {d['speaking_speed']:.0f} WPM, Filler Words: {d['filler_count']}, Long Pauses: {d['pause_count']})\n"
        f"- Strengths Identified: {strengths_text}\n"
        f"- Areas to Improve: {gaps_text}\n"
        f"- Technical Terms Missed: {missed}\n"
        f"- Answer Components Missing: {missing}\n\n"
        f"INSTRUCTIONS:\n"
        f"Write 3-4 sentences of natural, conversational, and coaching-style feedback. "
        f"Focus on:\n"
        f"1. What the candidate did well (be specific to their response)\n"
        f"2. Specific, actionable improvements based on their actual answer\n"
        f"3. Encouraging tone with practical tips\n\n"
        f"Feedback:"
    )


# ─── Strengths derived from scores ────────────────────────────────────────────
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
    if d["filler_count"] == 0:
        strengths.append("Confident delivery — no filler words detected.")
    if 120 <= d["speaking_speed"] <= 155:
        strengths.append("Excellent speaking pace (120–155 WPM).")
    return strengths or ["Keep practising — improvement takes consistent effort."]


# ─── Improvements list (coaching tips + gaps) ──────────────────────────────────
def _derive_improvements(d: dict) -> list[str]:
    improvements = list(d["coaching_tips"])
    if d["missed_keywords"]:
        improvements.append(
            f"Use these technical terms in your answer: {', '.join(d['missed_keywords'])}."
        )
    if d["components_missing"]:
        improvements.append(
            f"Strengthen your answer by adding: {', '.join(d['components_missing'])}."
        )
    return improvements


# ─── Main entry point ─────────────────────────────────────────────────────────
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
    """
    Combines all scoring outputs into a single structured feedback response.

    Returns:
        - answer_quality_score: 0-100 (breakdown: semantic, keyword, completeness)
        - confidence_score: 0-100 (breakdown: grammar, speaking_speed, filler_count, pause_count)
        - narrative_feedback: AI-generated coaching feedback
        - strengths: List of identified strengths
        - improvements: List of actionable improvements
    """
    # ── Derive strengths and improvements first (needed for prompt) ──────────
    strengths = _derive_strengths({
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "completeness_score": completeness_score,
        "grammar_score": grammar_score,
        "filler_count": filler_count,
        "speaking_speed": speaking_speed,
    })
    improvements = _derive_improvements({
        "coaching_tips": coaching_tips,
        "missed_keywords": missed_keywords,
        "components_missing": components_missing,
    })

    d = {
        "transcript": transcript,
        "answer_quality_score": answer_quality_score,
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "completeness_score": completeness_score,
        "confidence_score": confidence_score,
        "grammar_score": grammar_score,
        "speaking_speed": speaking_speed,
        "filler_count": filler_count,
        "pause_count": pause_count,
        "missed_keywords": missed_keywords,
        "components_missing": components_missing,
        "coaching_tips": coaching_tips,
        "strengths": strengths,
        "improvements": improvements,
    }

    # ── FLAN-T5 narrative (lazy-loaded on first call) ─────────────────────────
    try:
        prompt = _build_prompt(d)
        gen    = _get_generator()
        output = gen(
            prompt,
            max_new_tokens=200,
            num_beams=4,            # beam search → better quality than greedy
            early_stopping=True,
            no_repeat_ngram_size=3, # prevents repetitive phrases
        )
        narrative = output[0]["generated_text"].strip()
    except Exception as e:
        narrative = f"Feedback generation unavailable: {e}"

    # ── Structured sections (SIMPLIFIED for frontend) ───────────────────────
    return {
        # Top-level scores (what frontend displays first)
        "answer_quality_score": answer_quality_score,
        "confidence_score": confidence_score,
        
        # Score breakdowns (for expandable details)
        "answer_quality_breakdown": {
            "semantic": semantic_score,
            "keywords": keyword_score,
            "completeness": completeness_score,
        },
        "confidence_breakdown": {
            "grammar": grammar_score,
            "speaking_speed": speaking_speed,
            "filler_count": filler_count,
            "pause_count": pause_count,
        },

        # Qualitative feedback (for dashboard display)
        "narrative_feedback": narrative,
        "strengths": strengths,
        "improvements": improvements,
    }
