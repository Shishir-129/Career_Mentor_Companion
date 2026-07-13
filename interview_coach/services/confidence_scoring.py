import re
from typing import Optional

import librosa

# ─── Filler word bank ─────────────────────────────────────────────────────────
# Excludes context-dependent words like "so", "well", "like"
FILLER_WORDS = {
    "um", "uh", "ah", "eh", "hmm", "humm",
    "you know", "i mean", "kind of", "sort of",
    "literally", "basically", "actually", "right",
}

# ─── Score weights — must sum to 1.0 ─────────────────────────────────────────
# Grammar  35%: language quality, most evaluated by interviewers
# Filler   30%: nervousness signal, highly noticeable
# Pace     20%: clarity of delivery
# Pause    15%: hesitation — some pauses are natural
WEIGHTS = {
    "grammar": 0.35,
    "filler":  0.30,
    "pace":    0.20,
    "pause":   0.15,
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


def _grammar_score(text: str) -> float:
    """
    Grammar quality proxy (no heavy NLP library needed):
      1. Type-token ratio  — vocabulary diversity (higher = richer language)
      2. Avg sentence length — 8–20 words/sentence is natural in speech
      3. Consecutive word repetition penalty — catches stuttering
    Returns 0.0 – 1.0.
    """
    tokens = _normalize_tokens(text)
    word_count = len(tokens)
    if word_count < 3:
        return 0.2

    # 1. Vocabulary diversity
    ttr = len(set(tokens)) / word_count

    # 2. Sentence length naturalness
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    avg_len = word_count / max(len(sentences), 1)
    if 8 <= avg_len <= 20:
        length_score = 1.0
    elif 5 <= avg_len <= 30:
        length_score = 0.7
    else:
        length_score = 0.4

    # 3. Stuttering penalty
    repetitions = sum(1 for i in range(1, len(tokens)) if tokens[i] == tokens[i - 1])
    penalty = min(repetitions * 0.1, 0.3)

    score = (ttr * 0.5) + (length_score * 0.5) - penalty
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


def _pause_score(pause_count: int, duration_secs: float) -> float:
    """
    Rate-based (pauses per minute) so longer answers aren't
    unfairly penalised. Neutral score when no audio is available.
    """
    if duration_secs <= 0:
        return 0.5
    rate = pause_count / (duration_secs / 60.0)
    if rate <= 3:  return 1.0    # ≤3/min: natural
    if rate <= 6:  return 0.75   # 3–6/min: acceptable
    if rate <= 10: return 0.5    # 6–10/min: fair
    if rate <= 15: return 0.25   # 10–15/min: poor
    return 0.1                    # >15/min: very poor


def _count_fillers(tokens: list[str], text_lower: str) -> int:
    """Handles both single-word and multi-word fillers correctly."""
    count  = sum(1 for t in tokens if t in _FILLER_SINGLE)
    count += sum(text_lower.count(p) for p in _FILLER_MULTI)
    return count


def analyze_audio(audio_path: str) -> dict:
    """
    Librosa-only analysis: extracts duration and hesitation pause count.
    Designed to run in parallel with Whisper since both only need the audio
    file and are completely independent of each other.
    """
    duration_secs = 0.0
    pause_count   = 0
    try:
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        duration_secs = len(y) / sr if sr else 0.0
        if len(y) > 0:
            intervals = librosa.effects.split(y, top_db=30)
            for i in range(1, len(intervals)):
                gap_secs = (intervals[i][0] - intervals[i - 1][1]) / sr
                if gap_secs >= 1.0:   # only genuine hesitation pauses (>1s)
                    pause_count += 1
    except Exception:
        pass
    return {"duration_secs": duration_secs, "pause_count": pause_count}


def compute_delivery_scores(transcript: str, duration_secs: float, pause_count: int) -> dict:
    """
    Computes all delivery scores from transcript text + pre-computed audio data.
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

    grammar_s = _grammar_score(transcript)
    pace_s    = _pace_score(wpm)
    filler_s  = _filler_score(filler_count, word_count)
    pause_s   = _pause_score(pause_count, duration_secs)

    raw = (
        grammar_s * WEIGHTS["grammar"] +
        filler_s  * WEIGHTS["filler"]  +
        pace_s    * WEIGHTS["pace"]    +
        pause_s   * WEIGHTS["pause"]
    )
    confidence_score = round(raw * 100, 2)
    grammar_score    = round(grammar_s * 100, 2)

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




