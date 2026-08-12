import random
from sqlalchemy.orm import Session
from database.models import Questions
from crud.question_history import increment_question_seen

# Difficulty adjacency — controls fallback ordering
_DIFFICULTY_ORDER = ["easy", "medium", "hard"]


def get_questions_for_session(
    db: Session,
    user_id: int,
    role: str,
    level: str,
    interview_type: str,
    count: int = 5,
    difficulty: str = "Medium",
) -> list:
    """
    Smart question selection pipeline:
      1. Filter by role + experience_level + question_type + difficulty (exact)
      2. Expand to adjacent difficulty levels if pool is too small
      3. Apply greedy semantic diversity: each next question must be
         maximally different in meaning from the ones already chosen
      4. Freshness bonus: deprioritize questions asked many times before
      5. Track usage via times_asked so repeat questions are rare
    """
    level           = level.lower().strip()
    difficulty_norm = difficulty.lower().strip()
    interview_type  = interview_type.strip()

    # ── 1. Build candidate pool ──────────────────────────────────────────────
    candidates = _fetch_candidates(db, role, level, interview_type, difficulty_norm)

    if not candidates:
        return []

    # ── 2. Select using semantic diversity ───────────────────────────────────
    if len(candidates) <= count:
        selected = candidates
    else:
        selected = _diverse_select(candidates, count, difficulty_norm)

    # ── 3. Increment times_asked so future sessions see fresh questions ───────
    # AND track in user_question_history for user-specific analytics
    for q in selected:
        q.times_asked = (q.times_asked or 0) + 1
        # Track this question as seen by this user
        increment_question_seen(db, user_id, q.id)
    db.commit()

    return selected


def _fetch_candidates(db, role, level, interview_type, difficulty_norm):
    """
    Builds a candidate pool with progressive fallbacks:
      Pass 1: exact role + level + type + difficulty (strict)
      Pass 2: include adjacent difficulty levels
      Pass 3: drop interview_type constraint
      Pass 4: drop experience_level constraint
    """
    base = (
        db.query(Questions)
        .filter(
            Questions.role == role,
            Questions.question_text.isnot(None),
            Questions.ideal_answer.isnot(None),
            Questions.code_expected == False,
        )
    )

    # Adjacent difficulties (e.g. medium → [easy, medium, hard]; hard → [medium, hard])
    idx = _DIFFICULTY_ORDER.index(difficulty_norm) if difficulty_norm in _DIFFICULTY_ORDER else 1
    adjacent = _DIFFICULTY_ORDER[max(0, idx - 1): idx + 2]  # up to 3 levels

    # Pass 1: strict
    candidates = (
        base
        .filter(
            Questions.experience_level == level,
            Questions.question_type.ilike(f"%{interview_type}%"),
            Questions.difficulty.ilike(difficulty_norm),
        )
        .limit(80)
        .all()
    )
    if len(candidates) >= 5:
        return candidates

    # Pass 2: loosen difficulty to adjacent levels
    candidates = (
        base
        .filter(
            Questions.experience_level == level,
            Questions.question_type.ilike(f"%{interview_type}%"),
            Questions.difficulty.in_(adjacent),
        )
        .limit(80)
        .all()
    )
    if len(candidates) >= 5:
        return candidates

    # Pass 3: drop interview_type filter
    candidates = (
        base
        .filter(
            Questions.experience_level == level,
            Questions.difficulty.in_(adjacent),
        )
        .limit(80)
        .all()
    )
    if len(candidates) >= 1:
        return candidates

    # Pass 4: drop experience_level filter too
    return (
        base
        .filter(Questions.difficulty.in_(adjacent))
        .limit(80)
        .all()
    )


def _diverse_select(candidates: list, count: int, difficulty_norm: str) -> list:
    """
    Greedy maximum-diversity selection using sentence-transformer embeddings.

    Priority score for seeding and tiebreaking:
      - Exact difficulty match   → +0.20
      - Verified question        → +0.10
      - Never shown before       → +0.15  (times_asked == 0)
      - Each prior showing       → -0.05  (up to -0.30)

    After seeding, each successive pick is the candidate with the highest
    (semantic_diversity + priority_boost) score, ensuring the final set
    covers different topics and concepts.

    Falls back to priority-sorted selection if the model is unavailable.
    """
    try:
        from services.semantic_score import get_model
        from sentence_transformers import util

        model = get_model()  # already warm — zero reload cost
        texts = [q.question_text or "" for q in candidates]
        embeddings = model.encode(
            texts, convert_to_tensor=True, show_progress_bar=False
        )

        def _priority(i: int) -> float:
            q = candidates[i]
            score = 0.0
            if (q.difficulty or "").lower() == difficulty_norm:
                score += 0.20
            asked = q.times_asked or 0
            if asked == 0:
                score += 0.15
            else:
                score -= min(asked * 0.05, 0.30)  # penalty caps at -0.30
            return score

        # Seed: highest priority question
        seed = max(range(len(candidates)), key=_priority)
        selected = [seed]

        while len(selected) < count:
            best_idx, best_score = -1, -1.0
            for i in range(len(candidates)):
                if i in selected:
                    continue
                # Semantic diversity: 1 - max similarity to any already-selected
                sims = [
                    util.cos_sim(embeddings[i], embeddings[j]).item()
                    for j in selected
                ]
                diversity = 1.0 - max(sims)
                score = diversity + _priority(i)
                if score > best_score:
                    best_score, best_idx = score, i

            selected.append(best_idx)

        return [candidates[i] for i in selected]

    except Exception:
        # Fallback: sort by priority (difficulty match + freshness) if model fails
        def _fallback_priority(q):
            score = 0
            if (q.difficulty or "").lower() == difficulty_norm:
                score += 3
            score -= (q.times_asked or 0)
            return -score  # negate for ascending sort

        sorted_cands = sorted(candidates, key=_fallback_priority)
        return sorted_cands[:count]
