// frontend/src/pages/WeakAreas.jsx
import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./WeakAreas.css";
import { BASE_URL, getUserId } from "../api/config";

// Each scoring dimension: what it measures and what to do when it's low
const DIMENSIONS = [
    {
        key: "semantic_avg",
        label: "Conceptual Understanding",
        desc: "How closely your answer captures the meaning of an ideal response.",
        advice: [
            "Study the core concept deeply, not just its definition — understand the why.",
            "Practise explaining topics in your own words without notes.",
            "After answering, compare your explanation to a reference and note the gaps.",
        ],
    },
    {
        key: "keyword_avg",
        label: "Technical Vocabulary",
        desc: "Use of precise domain-specific terms that interviewers expect to hear.",
        advice: [
            "Build a glossary of key terms for your target role and review it regularly.",
            "Use exact terms — e.g. 'gradient descent' not 'the training process'.",
            "After each session, note which keywords you missed and practise using them.",
        ],
    },
    {
        key: "completeness_avg",
        label: "Answer Structure",
        desc: "Whether your answer covers key components: definition, example, use case.",
        advice: [
            "Use the Define → Explain → Example framework for every technical question.",
            "Always include a concrete real-world example in your answer.",
            "Before finishing, ask: did I define it, explain it, and give an example?",
        ],
    },
    {
        key: "confidence_avg",
        label: "Delivery & Confidence",
        desc: "Speaking pace, filler word rate, and hesitation pauses.",
        advice: [
            "Target 120–155 WPM — practise reading text aloud at that pace.",
            "Record yourself and count filler words like 'um', 'uh', 'basically'.",
            "Pause deliberately instead of filling silence — a 1-second pause sounds confident.",
        ],
    },
    {
        key: "grammar_avg",
        label: "Language Clarity",
        desc: "Grammatical correctness and natural sentence structure.",
        advice: [
            "Use shorter sentences (8–15 words) — they are easier to follow.",
            "Avoid repeating the same opening word in consecutive sentences.",
            "Read your transcript after each session and rewrite any awkward sentences.",
        ],
    },
];

function getScoreColor(score) {
    if (score < 50) return { color: "#ef4444", bg: "#fef2f2", border: "#fecaca", label: "Needs Work" };
    if (score < 65) return { color: "#f97316", bg: "#fff7ed", border: "#fed7aa", label: "Below Average" };
    if (score < 80) return { color: "#eab308", bg: "#fefce8", border: "#fef08a", label: "Average" };
    return { color: "#22c55e", bg: "#f0fdf4", border: "#bbf7d0", label: "Good" };
}

export default function WeakAreas() {
    const navigate = useNavigate();
    const [scores, setScores] = useState(null); // averaged scores across completed sessions
    const [sessionCount, setSessionCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState(null);
    const userId = getUserId();

    useEffect(() => { fetchData(); }, []);

    const fetchData = async () => {
        try {
            // ✅ Fetch pre-calculated weak areas by topic from backend
            const weakAreasRes = await axios.get(`${BASE_URL}/weak-areas/user/${userId}`);
            const weakAreas = weakAreasRes.data;
            
            // Get session count for display
            const sessionsRes = await axios.get(`${BASE_URL}/sessions/user/${userId}/history`);
            const sessionCount = sessionsRes.data.filter(s => s.completed).length;
            setSessionCount(sessionCount);

            if (weakAreas.length === 0) {
                setScores(null);
                return;
            }

            // Aggregate scores across all topics to show global skill breakdown
            const aggregateScores = (weakAreas) => {
                if (!weakAreas.length) return null;
                
                return {
                    semantic_avg: Math.round(
                        weakAreas.reduce((sum, wa) => sum + (wa.semantic_avg || 0), 0) / weakAreas.length
                    ),
                    keyword_avg: Math.round(
                        weakAreas.reduce((sum, wa) => sum + (wa.keyword_avg || 0), 0) / weakAreas.length
                    ),
                    completeness_avg: Math.round(
                        weakAreas.reduce((sum, wa) => sum + (wa.completeness_avg || 0), 0) / weakAreas.length
                    ),
                    confidence_avg: Math.round(
                        weakAreas.reduce((sum, wa) => sum + (wa.confidence_avg || 0), 0) / weakAreas.length
                    ),
                    grammar_avg: Math.round(
                        weakAreas.reduce((sum, wa) => sum + (wa.grammar_avg || 0), 0) / weakAreas.length
                    ),
                };
            };

            setScores(aggregateScores(weakAreas));
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // Sort: weakest first
    const sorted = scores
        ? [...DIMENSIONS].sort((a, b) => (scores[a.key] || 0) - (scores[b.key] || 0))
        : DIMENSIONS;

    if (loading) return (
        <div className="app-layout">
            <Sidebar />
            <div className="wa-wrapper wa-center"><p className="loading-text">⏳ Analysing your scores…</p></div>
        </div>
    );

    return (
        <div className="app-layout">
            <Sidebar />
            <div className="wa-wrapper">

                <div className="wa-header">
                    <div>
                        <h1>Skill Analysis</h1>
                        <p className="wa-sub">
                            {sessionCount === 0
                                ? "Complete at least one interview session to see your skill breakdown."
                                : `Based on ${sessionCount} completed session${sessionCount !== 1 ? "s" : ""}. Sorted by lowest score first.`}
                        </p>
                    </div>
                    {sessionCount === 0 && (
                        <button className="btn-primary" onClick={() => navigate("/new-interview")}>
                            Start Interview
                        </button>
                    )}
                </div>

                {sessionCount === 0 ? (
                    <div className="wa-empty">
                        <p>No completed sessions yet. Your skill breakdown will appear here after your first interview.</p>
                    </div>
                ) : (
                    <div className="wa-list">
                        {sorted.map(dim => {
                            const score = scores[dim.key] || 0;
                            const style = getScoreColor(score);
                            const isOpen = expanded === dim.key;

                            return (
                                <div
                                    key={dim.key}
                                    className="wa-card"
                                    style={{ borderColor: score < 65 ? style.border : "#e5e7eb" }}
                                >
                                    <div className="wa-card-top" onClick={() => setExpanded(isOpen ? null : dim.key)}>
                                        <div className="wa-card-left">
                                            <div className="wa-label-row">
                                                <span className="wa-dim-label">{dim.label}</span>
                                                <span
                                                    className="wa-status-badge"
                                                    style={{ color: style.color, background: style.bg, border: `1px solid ${style.border}` }}
                                                >
                                                    {style.label}
                                                </span>
                                            </div>
                                            <p className="wa-dim-desc">{dim.desc}</p>
                                            <div className="wa-bar-wrap">
                                                <div className="wa-bar">
                                                    <div
                                                        className="wa-bar-fill"
                                                        style={{ width: `${score}%`, background: style.color }}
                                                    />
                                                </div>
                                                <span className="wa-bar-label">{score}/100</span>
                                            </div>
                                        </div>
                                        <div className="wa-score-badge" style={{ color: style.color }}>
                                            {score}
                                        </div>
                                    </div>

                                    {isOpen && (
                                        <div className="wa-advice">
                                            <p className="wa-advice-title">How to improve:</p>
                                            <ul>
                                                {dim.advice.map((tip, i) => (
                                                    <li key={i}>{tip}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}

