import math
import re
from typing import Optional

import librosa
import numpy as np

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
    'basically',
    'literally',
    'seriously',

}


def _normalize_text(text: Optional[str]) -> list[str]:
    if not text:
        return []
    return re.findall(r"[a-z0-9']+", text.lower())


def _overlap_score(text: Optional[str], target: Optional[str]) -> float:
    tokens = set(_normalize_text(text))
    target_tokens = set(_normalize_text(target))
    if not tokens or not target_tokens:
        return 0.0

    overlap = len(tokens & target_tokens)
    return round(overlap / max(len(target_tokens), 1), 2)


def _extract_keywords(keywords: Optional[str]) -> list[str]:
    if not keywords:
        return []
    return [item.strip().lower() for item in str(keywords).split(",") if item.strip()]


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
            "semantic_score": 0.0,
            "keyword_score": 0.0,
            "grammar_score": 0.0,
            "relevance_score": 0.0,
            "confidence_score": 0.0,
            "final_score": 0.0,
            "speaking_speed": 0.0,
            "pause_count": 0,
            "filler_count": 0,
            "missed_keywords": "",
            "llm_feedback": "No transcript detected.",
        }

    duration = 0.0
    pause_count = 0
    filler_count = 0

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

    filler_count = sum(1 for token in tokens if token in FILLER_WORDS)

    context_text = " ".join(
        part for part in [question_text, ideal_answer, keywords] if part
    )
    keyword_tokens = _extract_keywords(keywords)
    keyword_target = " ".join(keyword_tokens or _normalize_text(context_text))

    relevance_score = _overlap_score(transcript, context_text)
    keyword_score = _overlap_score(transcript, keyword_target)

    semantic_score = round(min(1.0, 0.4 + (relevance_score * 0.4) + (0.2 if word_count >= 6 else 0.0)), 2)

    sentence_endings = sum(1 for char in transcript if char in ".!?")
    grammar_score = round(min(1.0, 0.45 + min(0.25, sentence_endings * 0.05) + min(0.2, max(0, word_count - 5) * 0.01)), 2)

    speaking_speed = round(word_count / max(duration / 60.0, 1e-6), 2) if duration > 0 else 0.0
    confidence_score = round(min(1.0, 0.3 + (relevance_score * 0.3) + (0.2 if word_count >= 8 else word_count * 0.025)), 2)

    final_score = round(
        min(
            1.0,
            (semantic_score * 0.35)
            + (keyword_score * 0.25)
            + (grammar_score * 0.2)
            + (relevance_score * 0.2),
        ),
        2,
    )

    missed_keywords = ", ".join(
        keyword for keyword in keyword_tokens if keyword not in set(tokens)
    )

    feedback_parts = []
    if final_score >= 0.8:
        feedback_parts.append("Strong answer quality.")
    elif final_score >= 0.6:
        feedback_parts.append("Good content but can be more precise.")
    else:
        feedback_parts.append("Response needs more structure and relevant detail.")

    if filler_count > 0:
        feedback_parts.append(f"Try reducing filler words ({filler_count}).")
    if pause_count > 2:
        feedback_parts.append("Pauses are frequent; speak a bit more smoothly.")

    return {
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "grammar_score": grammar_score,
        "relevance_score": relevance_score,
        "confidence_score": confidence_score,
        "final_score": final_score,
        "speaking_speed": speaking_speed,
        "pause_count": pause_count,
        "filler_count": filler_count,
        "missed_keywords": missed_keywords,
        "llm_feedback": " ".join(feedback_parts),
    }
