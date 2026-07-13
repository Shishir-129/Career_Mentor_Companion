import json
from services.completeness_score import COMPONENT_PATTERNS

_ALL_COMPONENTS = list(COMPONENT_PATTERNS.keys())


def generate_expected_components(ideal_answer: str) -> str | None:
    """
    Detects which structural components are present in the ideal_answer
    using the same phrase patterns used during scoring.

    This keeps seeding and scoring 100% consistent:
    if a pattern doesn't fire on the ideal answer, it won't fire on
    the user's answer either — so we never penalise unfairly.

    Returns a JSON string e.g. '["definition","example"]'
    ready to store in the DB, or None if answer is empty.
    """
    if not ideal_answer or not ideal_answer.strip():
        return None

    answer_lower = ideal_answer.lower()
    found = [
        component
        for component in _ALL_COMPONENTS
        if any(phrase in answer_lower for phrase in COMPONENT_PATTERNS[component])
    ]

    return json.dumps(found)

