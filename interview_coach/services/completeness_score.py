import json

# Component → trigger phrases (all matched case-insensitively as substrings)
COMPONENT_PATTERNS: dict[str, list[str]] = {
    "definition": [
        "is a ", "is an ", " means ", "refers to", "defined as",
        "stands for", "is the ", "is when", "is called", "known as",
    ],
    "example": [
        "for example", "such as", "for instance", "e.g.",
        "consider ", "suppose ", "like ", "to illustrate",
    ],
    "explanation": [
        "because", "therefore", "which means", "this is because",
        "as a result", "due to", "since ", "thus ", "hence ",
    ],
    "comparison": [
        "whereas", " while ", "however", "unlike", "compared to",
        "on the other hand", "in contrast", "instead",
    ],
    "use_case": [
        "used when", "used for", "useful when", "in practice",
        "in production", "we use", "applied to",
        "commonly used", "typically used",
    ],
    "limitation": [
        "limitation", "downside", "drawback", "does not work","however",
        "cannot", "weakness", "trade-off", "tradeoff",
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


def compute_completeness_score(
    user_answer: str,
    expected_components_json: str | None,
    ideal_answer: str | None = None,
) -> dict:
    """
    Returns:
        completeness_score  — float 0-100
        components_found    — list[str]
        components_missing  — list[str]
        coaching_tips       — list[str]  (one tip per missing component)

    NOTE: expected_components are first verified against the ideal_answer.
    If the ideal answer itself doesn't demonstrate a component, that component
    is dropped — we never penalise the user for something the reference
    answer doesn't cover either.
    """
    try:
        answer_lower = user_answer.lower() if user_answer else ""
        word_count = len(answer_lower.split()) if answer_lower.strip() else 0

        # ── Resolve which components the ideal answer actually covers ───────────
        expected = _parse_expected(expected_components_json)
        if expected and ideal_answer and ideal_answer.strip():
            ideal_lower = ideal_answer.lower()
            verified_found, _ = _detect_components(ideal_lower, expected)
            # Only keep components the ideal answer itself demonstrates
            expected = verified_found

        # ── Edge case: no expected_components (or none verified in ideal) ───────
        if not expected:
            score = 100.0 if word_count >= 3 else 20.0
            return {
                "completeness_score": score,
                "components_found": [],
                "components_missing": [],
                "coaching_tips": [],
            }

        # ── Edge case: empty user answer ────────────────────────────────────────
        if not answer_lower.strip():
            return {
                "completeness_score": 0.0,
                "components_found": [],
                "components_missing": expected,
                "coaching_tips": [COACHING_TIPS.get(c, "") for c in expected],
            }

        found, missing = _detect_components(answer_lower, expected)
        score = round((len(found) / len(expected)) * 100, 2)

        return {
            "completeness_score": score,
            "components_found": found,
            "components_missing": missing,
            "coaching_tips": [COACHING_TIPS.get(c, "") for c in missing],
        }
    except Exception as e:
        print(f"❌ Completeness scoring error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        # Return safe default on error
        return {
            "completeness_score": 50.0,
            "components_found": [],
            "components_missing": [],
            "coaching_tips": [],
        }


def _parse_expected(raw: str | None) -> list[str]:
    """Safely parse the JSON string from DB into a list."""
    if not raw or not raw.strip():
        return []
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
