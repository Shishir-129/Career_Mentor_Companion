import re
from typing import Optional

import librosa

FILLER_WORDS = {
    "ah",
    "eh",
    "um",
    "uh",
    "like",
    "you know",
    "actually",
    "basically",
    "so",
    "humm",
    "hmm",
    "well",
    "literally",
    "seriously",
}


def _normalize_text(text: Optional[str]) -> list[str]:
    if not text:
        return []
    return re.findall(r"[a-z0-9']+", text.lower())


def _grammar_score(text: str) -> float:
    tokens = _normalize_text(text)
    if not tokens:
        return 0.0

    sentence_endings = sum(1 for char in text if char in ".!?")
    capitalized_words = sum(1 for token in tokens if token[:1].isupper())

    score = 0.4
    if sentence_endings >= 1:
        score += 0.25
    if len(tokens) >= 8:
        score += 0.2
    if capitalized_words >= 1:
        score += 0.15

    return round(min(1.0, score), 2)


def score_transcript_audio(
    transcript: Optional[str],
    audio_path: Optional[str],
    question_text: Optional[str] = None,
    ideal_answer: Optional[str] = None,
    keywords: Optional[str] = None,
) -> dict:
    transcript = (transcript or "").strip()
    tokens = _normalize_text(transcript)
    word_count = len(tokens)

    if not transcript:
        return {
            "grammar_score": 0.0,
            "confidence_score": 0.0,
            "final_score": 0.0,
            "speaking_speed": 0.0,
            "pause_count": 0,
            "filler_count": 0,
            "llm_feedback": "No transcript detected.",
        }

    duration = 0.0
    pause_count = 0
    filler_count = sum(1 for token in tokens if token in FILLER_WORDS)

    try:
        if audio_path:
            audio_data, sample_rate = librosa.load(audio_path, sr=16000, mono=True)
            duration = len(audio_data) / sample_rate if sample_rate else 0.0

            if len(audio_data) > 0:
                silence_intervals = librosa.effects.split(audio_data, top_db=25)
                pause_count = max(0, len(silence_intervals) - 1)
    except Exception:
        duration = 0.0
        pause_count = 0

    speaking_speed = round(word_count / (duration / 60.0), 2) if duration > 0 else 0.0

    if 120 <= speaking_speed <= 180:
        pace_score = 1.0
    elif 90 <= speaking_speed <= 210:
        pace_score = 0.8
    elif 60 <= speaking_speed <= 240:
        pace_score = 0.6
    else:
        pace_score = 0.3

    if pause_count <= 1:
        pause_score = 1.0
    elif pause_count <= 3:
        pause_score = 0.8
    elif pause_count <= 5:
        pause_score = 0.6
    else:
        pause_score = 0.3

    if filler_count == 0:
        filler_score = 1.0
    elif filler_count <= 2:
        filler_score = 0.8
    elif filler_count <= 4:
        filler_score = 0.6
    else:
        filler_score = 0.3

    grammar_score = _grammar_score(transcript)
    confidence_score = round((pace_score * 0.25) + (pause_score * 0.25) + (filler_score * 0.25) + (grammar_score * 0.25), 2)
    final_score = confidence_score

    if confidence_score >= 0.8:
        outcome = "Excellent"
        feedback = "Strong confidence and delivery."
    elif confidence_score >= 0.6:
        outcome = "Good"
        feedback = "Solid delivery with a few improvements needed."
    elif confidence_score >= 0.4:
        outcome = "Fair"
        feedback = "Moderate confidence; improve pacing and reduce filler words."
    else:
        outcome = "Poor"
        feedback = "Low confidence and delivery quality."

    feedback_parts = [feedback]
    if filler_count > 0:
        feedback_parts.append(f"Filler words detected: {filler_count}.")
    if pause_count > 2:
        feedback_parts.append("Frequent pauses may reduce fluency.")

    feedback_parts.append(f"Confidence outcome: {outcome}.")

    return {
        "grammar_score": grammar_score,
        "confidence_score": confidence_score,
        "final_score": final_score,
        "speaking_speed": speaking_speed,
        "pause_count": pause_count,
        "filler_count": filler_count,
        "llm_feedback": " ".join(feedback_parts),
    }
