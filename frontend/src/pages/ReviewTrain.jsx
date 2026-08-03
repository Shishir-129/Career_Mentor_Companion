// frontend/src/pages/ReviewTrain.jsx
import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import "./ReviewTrain.css";
import { getUserId } from "../api/config";
import {
    getResponsesByUser,
    submitHumanFeedback,
    retrainScoringModel,
} from "../api/interviewApi";

const MIN_TRAINING_ROWS = 10; // must match MIN_TRAINING_ROWS in services/adaptive_scorer.py

export default function ReviewTrain() {
    const [responses, setResponses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [drafts, setDrafts] = useState({});      // { [responseId]: "85" }
    const [saving, setSaving] = useState({});       // { [responseId]: true }
    const [retraining, setRetraining] = useState(false);
    const [trainResult, setTrainResult] = useState(null);
    const userId = getUserId();

    useEffect(() => { fetchData(); }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const data = await getResponsesByUser(userId);
            setResponses(Array.isArray(data) ? data : []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const labeledCount = responses.filter(r => r.final_human_score != null).length;
    const canRetrain = labeledCount >= MIN_TRAINING_ROWS;

    const handleSave = async (responseId) => {
        const raw = drafts[responseId];
        const score = Number(raw);
        if (raw === "" || raw == null || Number.isNaN(score) || score < 0 || score > 100) {
            alert("Enter a score between 0 and 100.");
            return;
        }
        setSaving(s => ({ ...s, [responseId]: true }));
        try {
            const updated = await submitHumanFeedback(responseId, score);
            setResponses(rs => rs.map(r => (r.id === responseId ? updated : r)));
            setDrafts(d => { const next = { ...d }; delete next[responseId]; return next; });
        } catch (err) {
            console.error(err);
            alert("Failed to save score.");
        } finally {
            setSaving(s => ({ ...s, [responseId]: false }));
        }
    };

    const handleRetrain = async () => {
        setRetraining(true);
        setTrainResult(null);
        try {
            const result = await retrainScoringModel();
            setTrainResult(result);
        } catch (err) {
            console.error(err);
            setTrainResult({ status: "error" });
        } finally {
            setRetraining(false);
        }
    };

    return (
        <div className="app-layout">
            <Sidebar />
            <div className="rt-wrapper">
                <header className="rt-header">
                    <div>
                        <h1>Review &amp; Train</h1>
                        <p>Score real answers to teach the adaptive model what a good response looks like.</p>
                    </div>
                    <div className="rt-train-box">
                        <div className="rt-progress">
                            <strong>{labeledCount}</strong> / {MIN_TRAINING_ROWS} labeled
                            <div className="rt-progress-bar">
                                <div
                                    className="rt-progress-fill"
                                    style={{ width: `${Math.min(100, (labeledCount / MIN_TRAINING_ROWS) * 100)}%` }}
                                />
                            </div>
                        </div>
                        <button
                            className="rt-retrain-btn"
                            onClick={handleRetrain}
                            disabled={!canRetrain || retraining}
                            title={canRetrain ? "" : `Need at least ${MIN_TRAINING_ROWS} labeled answers`}
                        >
                            {retraining ? "Retraining…" : "Retrain model"}
                        </button>
                    </div>
                </header>

                {trainResult && (
                    <div className={`rt-banner rt-banner-${trainResult.status === "ok" ? "ok" : "warn"}`}>
                        {trainResult.status === "ok"
                            ? `✅ Model retrained on ${trainResult.trained_on} labeled answers.`
                            : trainResult.status === "not_enough_data"
                                ? `⚠️ Not enough labeled data yet (${trainResult.trained_on}/${MIN_TRAINING_ROWS}).`
                                : "❌ Retraining failed. Check the server logs."}
                    </div>
                )}

                {loading ? (
                    <p className="rt-loading">⏳ Loading answers…</p>
                ) : responses.length === 0 ? (
                    <p className="rt-empty">No answers to review yet. Complete an interview first.</p>
                ) : (
                    <div className="rt-list">
                        {responses.map((r) => (
                            <div key={r.id} className="rt-card">
                                <div className="rt-card-top">
                                    <span className="rt-topic">{r.topic || r.question_type || "Answer"} · #{r.id}</span>
                                    {r.final_human_score != null && (
                                        <span className="rt-labeled-badge">Labeled: {Math.round(r.final_human_score)}</span>
                                    )}
                                </div>

                                <p className="rt-transcript">{r.transcript || "[No transcript]"}</p>

                                <div className="rt-scores">
                                    <span>AI quality: <strong>{fmt(r.answer_quality_score)}</strong></span>
                                    <span>Predicted: <strong>{fmt(r.predicted_score)}</strong></span>
                                    <span>Semantic: <strong>{fmt(r.semantic_score)}</strong></span>
                                    <span>Keyword: <strong>{fmt(r.keyword_score)}</strong></span>
                                </div>

                                <div className="rt-actions">
                                    <input
                                        type="number"
                                        min="0"
                                        max="100"
                                        placeholder="Your score 0–100"
                                        value={drafts[r.id] ?? ""}
                                        onChange={(e) => setDrafts(d => ({ ...d, [r.id]: e.target.value }))}
                                    />
                                    <button
                                        onClick={() => handleSave(r.id)}
                                        disabled={saving[r.id]}
                                    >
                                        {saving[r.id] ? "Saving…" : "Save score"}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function fmt(v) {
    return v == null ? "—" : Math.round(v);
}
