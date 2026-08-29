import json
from sqlalchemy import or_
from sqlalchemy.orm import Session
from database.models import Questions, UserQuestionHistory, UserWeakAreas
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
      3. Hard-exclude questions already seen by this user (uses UserQuestionHistory)
      4. Boost priority for topics where the user has weak area scores
      5. Apply greedy semantic diversity: each next question must be
         maximally different in meaning from the ones already chosen
      6. Track usage via times_asked and user_question_history
    """
    level           = level.lower().strip()
    difficulty_norm = difficulty.lower().strip()
    interview_type  = interview_type.strip()

    # ── Load user-specific seen question ids ─────────────────────────────────
    seen_records = (
        db.query(UserQuestionHistory)
        .filter(UserQuestionHistory.user_id == user_id)
        .all()
    )
    seen_ids = {r.question_id for r in seen_records}

    # ── Load user weak area topic scores ─────────────────────────────────────
    weak_area_records = (
        db.query(UserWeakAreas)
        .filter(UserWeakAreas.user_id == user_id)
        .all()
    )
    # Build map: topic (lowercase) → overall avg score
    weak_topic_scores: dict[str, float] = {}
    for wa in weak_area_records:
        scores = [
            wa.semantic_avg or 0,
            wa.keyword_avg or 0,
            wa.completeness_avg or 0,
            wa.confidence_avg or 0,
            wa.grammar_avg or 0,
        ]
        weak_topic_scores[wa.topic.lower()] = sum(scores) / len(scores)

    # ── 1. Build candidate pool ───────────────────────────────────────────────
    candidates = _fetch_candidates(db, role, level, interview_type, difficulty_norm)
    # Reject questions that have no scorable reference answer at all
    candidates = [q for q in candidates if _has_reference_answer(q)]

    if not candidates:
        return []

    # ── 2. Prefer unseen questions; fall back to seen only if pool is too small
    unseen = [q for q in candidates if q.id not in seen_ids]
    if len(unseen) >= count:
        pool = unseen
    elif unseen:
        # Fill remaining slots from seen questions (least recently seen first)
        seen_candidates = [q for q in candidates if q.id in seen_ids]
        seen_candidates.sort(key=lambda q: next(
            (r.last_seen for r in seen_records if r.question_id == q.id),
            None
        ) or __import__('datetime').datetime.min)
        pool = unseen + seen_candidates
    else:
        pool = candidates  # no unseen at all — use everything

    # ── 3. Select using semantic diversity + weak area priority ───────────────
    if len(pool) <= count:
        selected = pool
    else:
        selected = _diverse_select(pool, count, difficulty_norm, weak_topic_scores)

    # ── 4. Increment usage counters ───────────────────────────────────────────
    for q in selected:
        q.times_asked = (q.times_asked or 0) + 1
        increment_question_seen(db, user_id, q.id)
    db.commit()

    return selected


def _has_reference_answer(q: Questions) -> bool:
    """True only if the question has at least one real reference answer to score against."""
    if q.ideal_answer and q.ideal_answer.strip():
        return True
    if q.answers:
        try:
            ans = q.answers if isinstance(q.answers, dict) else json.loads(q.answers)
            if ans.get("ideal", "") and str(ans["ideal"]).strip():
                return True
            if any(a and str(a).strip() for a in ans.get("alternatives", [])):
                return True
        except (ValueError, TypeError):
            pass
    return False


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
            or_(Questions.ideal_answer.isnot(None), Questions.answers.isnot(None)),
            Questions.code_expected == False,
        )
    )

    idx = _DIFFICULTY_ORDER.index(difficulty_norm) if difficulty_norm in _DIFFICULTY_ORDER else 1
    adjacent = _DIFFICULTY_ORDER[max(0, idx - 1): idx + 2]

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


def _diverse_select(
    candidates: list,
    count: int,
    difficulty_norm: str,
    weak_topic_scores: dict[str, float],
) -> list:
    """
    Greedy maximum-diversity selection using sentence-transformer embeddings.

    Priority score for seeding and tiebreaking:
      - Exact difficulty match          → +0.20
      - Never shown to this user before → +0.30  (unseen bonus — strong)
      - Weak area topic match           → +0.10 to +0.25 (scaled by weakness)
      - Each global prior showing       → -0.05  (up to -0.30)

    After seeding, each successive pick is the candidate with the highest
    (semantic_diversity + priority_boost) score.
    Falls back to priority-sorted selection if the model is unavailable.
    """
    def _priority(q: Questions) -> float:
        score = 0.0
        # Exact difficulty match bonus
        if (q.difficulty or "").lower() == difficulty_norm:
            score += 0.20
        # Global freshness penalty
        asked = q.times_asked or 0
        score -= min(asked * 0.05, 0.30)
        # Weak area topic boost — more weight for weaker topics
        topic = (q.topic or "").lower()
        if topic and topic in weak_topic_scores:
            topic_score = weak_topic_scores[topic]
            if topic_score < 50:
                score += 0.25   # needs work
            elif topic_score < 65:
                score += 0.18   # below average
            elif topic_score < 80:
                score += 0.10   # average — slight boost
        return score

    try:
        from services.semantic_score import get_model
        from sentence_transformers import util

        model = get_model()
        texts = [q.question_text or "" for q in candidates]
        embeddings = model.encode(
            texts, convert_to_tensor=True, show_progress_bar=False
        )

        # Seed: highest priority candidate
        seed = max(range(len(candidates)), key=lambda i: _priority(candidates[i]))
        selected = [seed]

        while len(selected) < count and len(selected) < len(candidates):
            best_idx, best_score = -1, -1.0
            for i in range(len(candidates)):
                if i in selected:
                    continue
                sims = [
                    util.cos_sim(embeddings[i], embeddings[j]).item()
                    for j in selected
                ]
                diversity = 1.0 - max(sims)
                score = diversity + _priority(candidates[i])
                if score > best_score:
                    best_score, best_idx = score, i

            selected.append(best_idx)

        return [candidates[i] for i in selected]

    except Exception:
        # Fallback: sort by priority if model fails
        sorted_cands = sorted(candidates, key=lambda q: -_priority(q))
        return sorted_cands[:count]
