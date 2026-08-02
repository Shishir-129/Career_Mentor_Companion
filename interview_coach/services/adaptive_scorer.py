import logging
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy.orm import Session

from database.models import Responses

log = logging.getLogger("uvicorn.error")

# ─── Model artifact location ──────────────────────────────────────────────────
MODEL_DIR = Path(__file__).resolve().parent.parent / "ml_models"
MODEL_PATH = MODEL_DIR / "scoring_model.pkl"

# ─── Feature order — shared constant used by BOTH predict() and retrain_from_db()
# A mismatch between training-time and prediction-time order is the most likely
# bug here, so this list must never be duplicated elsewhere.
FEATURE_COLUMNS = [
    "semantic_score",
    "keyword_score",
    "completeness_score",
    "grammar_score",
    "confidence_score",
    "speaking_speed",
    "pause_count",
    "filler_count",
]

MIN_TRAINING_ROWS = 10  # don't retrain on a statistically meaningless sample


class AdaptiveScorer:
    """
    Optional ML layer that sits beside the fixed scorers
    (compute_answer_quality_score / compute_delivery_scores) — never
    replaces them. When no trained model exists yet, predict() returns the
    fixed `answer_quality_score` unchanged, so behaviour is identical to
    today until enough human-reviewed feedback has been collected.
    """

    def __init__(self):
        self._model: RandomForestRegressor | None = None
        self.reload_model()

    def reload_model(self) -> None:
        """(Re)loads MODEL_PATH from disk. Called on init and again at the
        end of retrain_from_db() so a long-running API process picks up a
        freshly trained model without needing a restart."""
        if MODEL_PATH.exists():
            try:
                self._model = joblib.load(MODEL_PATH)
                log.info("AdaptiveScorer: loaded trained model from %s", MODEL_PATH)
            except Exception as exc:
                log.warning("AdaptiveScorer: failed to load model (%s) — using fixed scoring", exc)
                self._model = None
        else:
            log.info("AdaptiveScorer: no trained model found yet — using fixed scoring only")
            self._model = None

    def predict(self, features: dict, fallback_score: float) -> float:
        """
        Returns the ML-predicted score, or `fallback_score` unchanged if no
        model is trained yet or prediction fails for any reason. This runs
        inline in the live answer-submission request path, so it must never
        raise.
        """
        if self._model is None:
            return fallback_score

        try:
            row = [features.get(col) or 0.0 for col in FEATURE_COLUMNS]
            prediction = self._model.predict([row])[0]
            return float(prediction)
        except Exception as exc:
            log.warning("AdaptiveScorer: prediction failed (%s) — falling back to fixed score", exc)
            return fallback_score

    def record_human_feedback(
        self, db: Session, response_id: int, actual_score: float
    ) -> Responses | None:
        """Stores a mentor/reviewer's ground-truth score for later retraining."""
        response = db.query(Responses).filter(Responses.id == response_id).first()
        if not response:
            return None

        response.final_human_score = actual_score
        db.commit()
        db.refresh(response)
        return response

    def retrain_from_db(self, db: Session) -> dict:
        """
        Retrains the RandomForestRegressor on every human-labeled response
        and overwrites scoring_model.pkl. Skips training (instead of
        raising) if fewer than MIN_TRAINING_ROWS labeled rows exist yet.
        """
        rows = (
            db.query(Responses)
            .filter(Responses.final_human_score.isnot(None))
            .all()
        )

        if len(rows) < MIN_TRAINING_ROWS:
            msg = (
                f"Not enough labeled data to retrain "
                f"({len(rows)}/{MIN_TRAINING_ROWS} rows) — keeping current model."
            )
            log.info("AdaptiveScorer: %s", msg)
            return {"trained_on": len(rows), "status": "not_enough_data"}

        X = [[getattr(r, col) or 0.0 for col in FEATURE_COLUMNS] for r in rows]
        y = [r.final_human_score for r in rows]

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)

        MODEL_DIR.mkdir(exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        self.reload_model()

        log.info("AdaptiveScorer: retrained on %d labeled rows and saved to %s", len(rows), MODEL_PATH)
        return {"trained_on": len(rows), "status": "ok"}


# Module-level singleton — loaded once and reused across requests, same
# pattern as the module-level `_model` in services/semantic_score.py.
adaptive_scorer = AdaptiveScorer()
