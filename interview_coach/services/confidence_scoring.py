import re
from typing import Optional

import librosa

# ─── Stop words (shared with completeness scorer) ─────────────────────────────
_STOP_WORDS = {
    "the","a","an","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","could","should","may","might",
    "shall","can","to","of","in","for","on","with","at","by","from","up",
    "about","into","this","that","these","those","i","we","you","they","he",
    "she","it","my","our","your","their","its","and","or","but","if","when",
    "what","how","why","which","who","where","just","also","so","than","then",
    "very","too","some","any","all","most","more","such","no","not","only",
}

# ─── Filler word bank ─────────────────────────────────────────────────────────
# Excludes context-dependent words like "so", "well", "like"
FILLER_WORDS = {
    "um", "uh", "ah", "eh", "hmm", "umm", "uhh",
    "you know", "i mean", "kind of", "sort of",
    "literally", "basically", "actually", "right",
    "like i said", "and um", "and uh",
}

# ─── Score weights — must sum to 1.0 ─────────────────────────────────────────
# Grammar  45%: language quality, most evaluated by interviewers
# Filler    5%: Whisper cleans transcripts so filler count is unreliable
# Pace     25%: clarity of delivery
# Pause    25%: hesitation — detectable via librosa audio gaps
WEIGHTS = {
    "grammar": 0.45,
    "filler":  0.05,
    "pace":    0.25,
    "pause":   0.25,
}

# ─── Speaking pace bands (words per minute) ───────────────────────────────────
PACE_EXCELLENT = (120, 155)   # ideal interview delivery
PACE_GOOD      = (100, 175)
PACE_FAIR      = (85,  190)


# ─── Precomputed filler sets (split once at import, not on every call) ────────
_FILLER_SINGLE = {w for w in FILLER_WORDS if " " not in w}
_FILLER_MULTI  = {w for w in FILLER_WORDS if " " in w}


def _normalize_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _meaningful_tokens(text: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-z]+", text.lower())
        if t not in _STOP_WORDS and len(t) > 2
    }


def _substance_score(tokens: list[str], question_text: str) -> float:
    """
    Measures original content depth:
      - Ratio of meaningful tokens not shared with the question (original content)
      - Penalises very short answers and question-repeating answers
    Returns 0.0 – 1.0.
    """
    if not tokens:
        return 0.0
    meaningful  = {t for t in tokens if t not in _STOP_WORDS and len(t) > 2}
    q_tokens    = _meaningful_tokens(question_text) if question_text else set()
    original    = meaningful - q_tokens
    if not meaningful:
        return 0.1
    originality = len(original) / len(meaningful)
    # Short-answer penalty: < 12 words → cap originality benefit
    if len(tokens) < 8:
        return min(originality * 0.3, 0.3)
    if len(tokens) < 15:
        return originality * 0.6
    return originality


def _grammar_score(text: str, question_text: str = "") -> float:
    """
    Grammar / language quality proxy:
      1. Substance score (45%) — original content depth vs question repetition
      2. TTR (30%)             — vocabulary diversity (capped for short text)
      3. Sentence length (25%) — 8–20 words/sentence is natural in speech
      4. Repetition penalty    — consecutive identical words (stuttering)
    Returns 0.0 – 1.0.
    """
    tokens = _normalize_tokens(text)
    word_count = len(tokens)
    if word_count < 3:
        return 0.1

    # 1. Substance (original content vs question-repeat)
    substance = _substance_score(tokens, question_text)

    # 2. TTR — on short text a high TTR just means random words, so cap it
    ttr = len(set(tokens)) / word_count
    if word_count < 15 and ttr > 0.85:
        ttr = 0.55  # short random words look artificially diverse

    # 3. Sentence length naturalness
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    avg_len = word_count / max(len(sentences), 1)
    if 8 <= avg_len <= 20:
        length_score = 1.0
    elif 5 <= avg_len <= 30:
        length_score = 0.7
    else:
        length_score = 0.4

    # 4. Stuttering penalty
    repetitions = sum(1 for i in range(1, len(tokens)) if tokens[i] == tokens[i - 1])
    penalty = min(repetitions * 0.1, 0.3)

    score = substance * 0.45 + ttr * 0.30 + length_score * 0.25 - penalty
    return round(max(0.0, min(1.0, score)), 2)


def _pace_score(wpm: float) -> float:
    if PACE_EXCELLENT[0] <= wpm <= PACE_EXCELLENT[1]: return 1.0
    if PACE_GOOD[0]      <= wpm <= PACE_GOOD[1]:      return 0.75
    if PACE_FAIR[0]      <= wpm <= PACE_FAIR[1]:       return 0.5
    return 0.25


def _filler_score(filler_count: int, word_count: int) -> float:
    """
    Rate-based (fillers per 100 words) so a long answer isn't
    unfairly penalised for the same absolute count as a short one.
    """
    if word_count == 0:
        return 0.0
    rate = (filler_count / word_count) * 100
    if rate <= 1.0:  return 1.0    # ≤1 per 100 words: excellent
    if rate <= 3.0:  return 0.75   # 1–3: good
    if rate <= 6.0:  return 0.5    # 3–6: fair
    if rate <= 10.0: return 0.25   # 6–10: poor
    return 0.1                      # >10: very poor


def _pause_score(pause_count: int, duration_secs: float, total_pause_secs: float = 0.0) -> float:
    """
    Two-check scoring — final score is the worse of Q1 and Q2.

    Q1 (frequency): pauses per minute — catches too-many short pauses
    Q2 (ratio):     total silence / total duration — catches one long freeze

    Pause threshold (≥1s) is unchanged — only scoring is improved.
    """
    if duration_secs <= 0:
        return 0.5

    # Q1 — frequency check
    rate = pause_count / (duration_secs / 60.0)
    if rate <= 3:    q1 = 1.0
    elif rate <= 6:  q1 = 0.75
    elif rate <= 10: q1 = 0.50
    elif rate <= 15: q1 = 0.25
    else:            q1 = 0.10

    # Q2 — total silence ratio check
    ratio = total_pause_secs / duration_secs
    if ratio <= 0.05:   q2 = 1.0
    elif ratio <= 0.15: q2 = 0.75
    elif ratio <= 0.30: q2 = 0.50
    elif ratio <= 0.50: q2 = 0.25
    else:               q2 = 0.10

    return min(q1, q2)  # penalise on whichever is worse


def _count_fillers(tokens: list[str], text_lower: str) -> int:
    """Handles both single-word and multi-word fillers correctly."""
    count  = sum(1 for t in tokens if t in _FILLER_SINGLE)
    count += sum(text_lower.count(p) for p in _FILLER_MULTI)
    return count


def analyze_audio(audio_path: str) -> dict:
    """
    Librosa-only analysis: extracts duration, hesitation pause count,
    and total pause duration in seconds.
    Pause threshold (≥1s) is unchanged.
    """
    duration_secs    = 0.0
    pause_count      = 0
    total_pause_secs = 0.0
    try:
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        duration_secs = len(y) / sr if sr else 0.0
        if len(y) > 0:
            intervals = librosa.effects.split(y, top_db=30)
            for i in range(1, len(intervals)):
                gap_secs = (intervals[i][0] - intervals[i - 1][1]) / sr
                if gap_secs >= 1.0:        # only genuine hesitation pauses (>1s)
                    pause_count      += 1
                    total_pause_secs += gap_secs   # accumulate actual silence duration
    except Exception:
        pass
    return {
        "duration_secs":    duration_secs,
        "pause_count":      pause_count,
        "total_pause_secs": total_pause_secs,
    }


def compute_delivery_scores(
    transcript:       str,
    duration_secs:    float,
    pause_count:      int,
    question_text:    str   = "",
    total_pause_secs: float = 0.0,
) -> dict:
    """
    Computes all delivery scores from transcript text + pre-computed audio data.
    question_text is used to detect question-parroting in the grammar/substance score.
    total_pause_secs is the sum of all silence gap durations from analyze_audio().
    Call this after both Whisper and analyze_audio() have completed.
    """
    transcript = (transcript or "").strip()
    tokens     = _normalize_tokens(transcript)
    word_count = len(tokens)

    if not transcript:
        return {
            "grammar_score":    0.0,
            "confidence_score": 0.0,
            "speaking_speed":   0.0,
            "pause_count":      0,
            "filler_count":     0,
            "llm_feedback":     "No transcript detected.",
        }

    wpm          = round(word_count / (duration_secs / 60.0), 1) if duration_secs > 0 else 0.0
    filler_count = _count_fillers(tokens, transcript.lower())

    grammar_s = _grammar_score(transcript, question_text)
    pace_s    = _pace_score(wpm)
    filler_s  = _filler_score(filler_count, word_count)
    pause_s   = _pause_score(pause_count, duration_secs, total_pause_secs)

    raw = (
        grammar_s * WEIGHTS["grammar"] +
        filler_s  * WEIGHTS["filler"]  +
        pace_s    * WEIGHTS["pace"]    +
        pause_s   * WEIGHTS["pause"]
    )
    confidence_score = round(raw * 100, 2)
    grammar_score    = round(grammar_s * 100, 2)

    # Word-count gate: in a real interview, < 15 words is not a confident answer
    # regardless of how fluently those few words were delivered.
    if word_count < 8:
        confidence_score = min(confidence_score, 28.0)
    elif word_count < 15:
        cap = 28.0 + (word_count - 8) * (22.0 / 7)  # linearly 28→50 over 8-15 words
        confidence_score = min(confidence_score, round(cap, 2))

    if   confidence_score >= 85: label = "Excellent"
    elif confidence_score >= 65: label = "Good"
    elif confidence_score >= 45: label = "Fair"
    else:                        label = "Poor"

    tips = []
    if wpm > 0 and not (PACE_EXCELLENT[0] <= wpm <= PACE_EXCELLENT[1]):
        tips.append(
            f"Speaking pace is {wpm:.0f} WPM — "
            f"aim for {PACE_EXCELLENT[0]}–{PACE_EXCELLENT[1]} WPM."
        )
    if filler_count > 0:
        rate = round((filler_count / word_count) * 100, 1)
        tips.append(f"{filler_count} filler word(s) detected ({rate} per 100 words).")
    if duration_secs > 0 and (pause_count / (duration_secs / 60.0)) > 3:
        tips.append("Frequent hesitation pauses detected — practice smoother transitions between ideas.")

    feedback = f"Delivery: {label}. " + " ".join(tips) if tips else f"Delivery: {label}."

    return {
        "grammar_score":    grammar_score,
        "confidence_score": confidence_score,
        "speaking_speed":   wpm,
        "pause_count":      pause_count,
        "filler_count":     filler_count,
        "llm_feedback":     feedback,
    }


def score_transcript_audio(
    transcript: Optional[str],
    audio_path: Optional[str],
) -> dict:
    """
    Convenience wrapper — runs analyze_audio + compute_delivery_scores
    sequentially. Use analyze_audio() + compute_delivery_scores() directly
    when parallelising with Whisper transcription.
    """
    audio_data = analyze_audio(audio_path) if audio_path else {"duration_secs": 0.0, "pause_count": 0}
    return compute_delivery_scores(
        transcript=transcript or "",
        duration_secs=audio_data["duration_secs"],
        pause_count=audio_data["pause_count"],
    )




