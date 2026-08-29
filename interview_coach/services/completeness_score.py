import re
import json

# ─── Stop words for meaningful-token extraction ───────────────────────────────
_STOP_WORDS = {
    "the","a","an","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","could","should","may","might",
    "shall","can","to","of","in","for","on","with","at","by","from","up",
    "about","into","this","that","these","those","i","we","you","they","he",
    "she","it","my","our","your","their","its","and","or","but","if","when",
    "what","how","why","which","who","where","just","also","so","than","then",
    "very","too","some","any","all","most","more","such","no","not","only",
    "same","other","used","using","use","make","makes","made","way","ways",
}

# Component → trigger phrases (all matched case-insensitively as substrings)
COMPONENT_PATTERNS: dict[str, list[str]] = {
    "definition": [
        "is a ", "is an ", " means ", "refers to", "defined as",
        "stands for", "is the process", "is when", "is called", "known as",
    ],
    "example": [
        "for example", "such as", "for instance", "e.g.",
        "consider ", "suppose ", "to illustrate", "as an example",
    ],
    "explanation": [
        "because ", "therefore ", "which means", "this is because",
        "as a result", "due to ", "this happens", "thus, ", "hence, ",
    ],
    "comparison": [
        "whereas ", " while ", "however, ", "unlike ", "compared to",
        "on the other hand", "in contrast", "instead of",
    ],
    "use_case": [
        "used when", "used for", "useful when", "in practice",
        "in production", "commonly used", "typically used", "applied to",
    ],
    "limitation": [
        "limitation", "downside", "drawback", "does not work",
        "cannot ", "weakness", "trade-off", "tradeoff", "disadvantage",
    ],
}

# STAR components for behavioral questions (Situation, Task, Action, Result)
STAR_PATTERNS: dict[str, list[str]] = {
    "situation": [
        "was working", "was assigned", "faced", "encountered", "situation was",
        "context", "background", "challenge was", "the problem", "initially",
        "at the time", "team was", "company was", "my role was", "responsible for",
    ],
    "task": [
        "had to", "needed to", "tasked with", "asked to", "assigned to",
        "my responsibility", "my goal", "objective was", "aim was", "responsibility",
        "had to solve", "needed to address", "had to improve", "had to build",
    ],
    "action": [
        "i did", "i implemented", "i created", "i developed", "i worked",
        "i proposed", "i suggested", "i initiated", "i took", "i decided",
        "i analyzed", "i researched", "i collaborated", "we decided", "we implemented",
        "approached", "solution", "steps i took", "what i did", "how i",
    ],
    "result": [
        "resulted in", "led to", "improved", "increased", "reduced",
        "achieved", "accomplished", "successfully", "outcome was", "result was",
        "finished", "completed", "delivered", "learned", "gained", "discovered",
        "percent", "%", "times", "followers", "users", "metrics",
    ],
}

# Human-readable coaching tip for each missing component
COACHING_TIPS: dict[str, str] = {
    "definition":  "Try opening with a clear definition of the concept.",
    "example":     "Your answer would be stronger with a concrete example.",
    "explanation": "Explain the reasoning or mechanism behind your answer.",
    "comparison":  "Consider comparing this with a related concept.",
    "use_case":    "Your answer would be stronger with a real-world use case.",
    "limitation":  "Mention any limitations or trade-offs to show deeper understanding.",
}

# STAR coaching tips for behavioral questions
STAR_COACHING_TIPS: dict[str, str] = {
    "situation": "Describe the situation: What was the context? What team/project were you working on?",
    "task":      "Explain your task: What was your responsibility or goal?",
    "action":    "Detail your action: What specific steps did you take? How did you approach it?",
    "result":    "Quantify your result: What was the outcome? How did it impact the project or team?",
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _meaningful_tokens(text: str) -> set[str]:
    """Unique content words: lower-case alpha tokens, len > 2, not stop words."""
    return {
        t for t in re.findall(r"[a-z]+", text.lower())
        if t not in _STOP_WORDS and len(t) > 2
    }


def _parroting_ratio(answer_text: str, question_text: str) -> float:
    """
    Fraction of the answer's meaningful tokens that are also in the question.
    High value → user likely just repeated the question.
    """
    a_tok = _meaningful_tokens(answer_text)
    q_tok = _meaningful_tokens(question_text)
    if not a_tok:
        return 1.0
    if not q_tok:
        return 0.0
    return len(a_tok & q_tok) / len(a_tok)


def _keyword_coverage(answer_text: str, ideal_text: str) -> float:
    """
    Fraction of the ideal answer's meaningful tokens present in the user answer.
    Used when no expected_components are available.
    """
    i_tok = _meaningful_tokens(ideal_text)
    a_tok = _meaningful_tokens(answer_text)
    if not i_tok:
        return 0.0
    return len(i_tok & a_tok) / len(i_tok)


def _detect_components(
    answer_lower: str, expected: list[str]
) -> tuple[list[str], list[str]]:
    found, missing = [], []
    for component in expected:
        patterns = COMPONENT_PATTERNS.get(component, [])
        if any(p in answer_lower for p in patterns):
            found.append(component)
        else:
            missing.append(component)
    return found, missing


def _detect_star_components(answer_lower: str) -> tuple[list[str], list[str]]:
    """Detect STAR components for behavioral questions"""
    found, missing = [], []
    star_components = ["situation", "task", "action", "result"]
    
    for component in star_components:
        patterns = STAR_PATTERNS.get(component, [])
        if any(p in answer_lower for p in patterns):
            found.append(component)
        else:
            missing.append(component)
    
    return found, missing


# ─── Main scorer ──────────────────────────────────────────────────────────────

def compute_completeness_score(
    user_answer: str,
    expected_components_json: str | None,
    ideal_answer: str | None = None,
    question_text: str | None = None,
    alternatives: list[str] | None = None,
    question_type: str = "technical",
) -> dict:
    """
    Returns:
        completeness_score  — float 0-100
        components_found    — list[str]
        components_missing  — list[str]
        coaching_tips       — list[str]

    Scoring strategy:
      For Technical Questions:
        1. Parroting guard: if the user mostly repeated the question,
           cap the score at 20 regardless of other signals.
        2. Component-based path (preferred): score = found/expected × 100,
           then apply short-answer cap and parroting adjustment.
        3. Keyword-coverage path (no components): score = overlap(answer,
           ideal) weighted by length ratio, penalised for parroting/shortness.
      
      For Behavioral Questions:
        1. Always use STAR (Situation, Task, Action, Result) components
        2. Score = number of STAR components found / 4 × 100
        3. Apply parroting penalty if user just echoed the question
    """
    try:
        answer_lower = (user_answer or "").strip().lower()
        word_count   = len(answer_lower.split()) if answer_lower else 0
        is_behavioral = question_type.lower().strip() == "behavioral"

        # ── Parroting detection ─────────────────────────────────────────────
        parrot = _parroting_ratio(answer_lower, question_text or "")

        # ── Empty user answer ───────────────────────────────────────────────
        if not answer_lower:
            if is_behavioral:
                return _zero_result(["situation", "task", "action", "result"])
            else:
                expected = _parse_expected(expected_components_json)
                return _zero_result(expected)

        # ── Very short answer (< 8 words) ────────────────────────────────────
        if word_count < 8:
            if is_behavioral:
                _, missing = _detect_star_components(answer_lower)
                tips = [STAR_COACHING_TIPS.get(c, "") for c in missing]
            else:
                expected = _parse_expected(expected_components_json)
                missing = expected
                tips = [COACHING_TIPS.get(c, "") for c in expected] if expected else []
            
            return {
                "completeness_score": max(5.0, word_count * 2.0),
                "components_found":   [],
                "components_missing": missing,
                "coaching_tips":      tips,
            }

        # ── Behavioral: Use STAR components ─────────────────────────────────
        if is_behavioral:
            found, missing = _detect_star_components(answer_lower)
            score = (len(found) / 4) * 100  # 4 STAR components

            # Short answer penalty: < 30 words caps at 60
            if word_count < 30:
                score = min(score, 60.0)

            # Parroting penalty
            score = _apply_parrot_penalty(score, parrot)

            return {
                "completeness_score": round(score, 2),
                "components_found":   found,
                "components_missing": missing,
                "coaching_tips":      [STAR_COACHING_TIPS.get(c, "") for c in missing],
            }

        # ── Technical: Use expected components or keyword coverage ──────────
        # Resolve verified components
        expected = _parse_expected(expected_components_json)
        if expected and ideal_answer and ideal_answer.strip():
            ideal_lower = ideal_answer.lower()
            verified, _ = _detect_components(ideal_lower, expected)
            expected = verified  # drop components the ideal doesn't demonstrate

        # ── Path A: component-based ──────────────────────────────────────────
        if expected:
            found, missing = _detect_components(answer_lower, expected)
            score = (len(found) / len(expected)) * 100

            # Short answer penalty: < 20 words caps at 45
            if word_count < 20:
                score = min(score, 45.0)

            # Parroting penalty
            score = _apply_parrot_penalty(score, parrot)

            return {
                "completeness_score": round(score, 2),
                "components_found":   found,
                "components_missing": missing,
                "coaching_tips":      [COACHING_TIPS.get(c, "") for c in missing],
            }

        # ── Path B: keyword-coverage (no verified components) ───────────────
        if ideal_answer and ideal_answer.strip():
            # Use the best-matching candidate (ideal + alternatives)
            candidates = [ideal_answer] + [a for a in (alternatives or []) if a and a.strip()]
            best_coverage = max(_keyword_coverage(answer_lower, c) for c in candidates)
            # Length ratio based on the primary ideal answer
            ideal_wc      = len(ideal_answer.split())
            length_ratio  = min(word_count / max(ideal_wc * 0.4, 1), 1.0)
            score         = best_coverage * length_ratio * 100
        else:
            # No ideal and no components: can only judge length
            score = min(50.0, word_count * 1.5)

        score = _apply_parrot_penalty(score, parrot)
        return {
            "completeness_score": round(max(0.0, score), 2),
            "components_found":   [],
            "components_missing": [],
            "coaching_tips":      [],
        }

    except Exception as e:
        print(f"❌ Completeness scoring error: {type(e).__name__}: {e}")
        return {
            "completeness_score": 50.0,
            "components_found":   [],
            "components_missing": [],
            "coaching_tips":      [],
        }


def _apply_parrot_penalty(score: float, parrot: float) -> float:
    """Penalise scores when the answer is mainly a repetition of the question."""
    if parrot >= 0.70:
        return min(score, 18.0)   # essentially just echoed the question
    if parrot >= 0.55:
        return score * (1.0 - (parrot - 0.55) * 2.5)  # gradual reduction
    return score


def _zero_result(expected: list[str]) -> dict:
    return {
        "completeness_score": 0.0,
        "components_found":   [],
        "components_missing": expected,
        "coaching_tips":      [COACHING_TIPS.get(c, "") for c in expected],
    }


def _parse_expected(raw: str | None) -> list[str]:
    if not raw or not raw.strip():
        return []
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []

