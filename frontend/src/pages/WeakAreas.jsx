// frontend/src/pages/WeakAreas.jsx
import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./WeakAreas.css";
import { BASE_URL, getUserId } from "../api/config";

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
        behavioralExclude: true,  // Hide for behavioral-only topics
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
        behavioralExclude: true,  // Hide for behavioral-only topics
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

/** Compute a simple average of relevant dimensions for a single topic row */
function topicOverallScore(wa) {
    const isBehavioral = wa.is_behavioral_only;
    let vals = [wa.semantic_avg, wa.keyword_avg, wa.completeness_avg, wa.confidence_avg, wa.grammar_avg];
    
    // For behavioral-only topics, exclude semantic and keyword
    if (isBehavioral) {
        vals = [wa.completeness_avg, wa.confidence_avg, wa.grammar_avg];
    }
    
    return Math.round(vals.reduce((s, v) => s + (v || 0), 0) / vals.length);
}

/** Aggregate across all topic rows (unweighted avg per dimension) */
function buildOverall(weakAreas) {
    if (!weakAreas.length) return null;
    
    // Separate behavioral and technical topics
    const technicalAreas = weakAreas.filter(wa => !wa.is_behavioral_only);
    const behavioralAreas = weakAreas.filter(wa => wa.is_behavioral_only);
    
    // For technical: average all 5
    // For behavioral: average only 3
    const getTechAvg = (key) => technicalAreas.length 
        ? Math.round(technicalAreas.reduce((s, wa) => s + (wa[key] || 0), 0) / technicalAreas.length)
        : 0;
    const getBehavioralAvg = (key) => behavioralAreas.length
        ? Math.round(behavioralAreas.reduce((s, wa) => s + (wa[key] || 0), 0) / behavioralAreas.length)
        : 0;
    
    return {
        semantic_avg:     getTechAvg("semantic_avg"),
        keyword_avg:      getTechAvg("keyword_avg"),
        completeness_avg: Math.round((technicalAreas.reduce((s, wa) => s + (wa.completeness_avg || 0), 0) + behavioralAreas.reduce((s, wa) => s + (wa.completeness_avg || 0), 0)) / (weakAreas.length)),
        confidence_avg:   Math.round((technicalAreas.reduce((s, wa) => s + (wa.confidence_avg || 0), 0) + behavioralAreas.reduce((s, wa) => s + (wa.confidence_avg || 0), 0)) / (weakAreas.length)),
        grammar_avg:      Math.round((technicalAreas.reduce((s, wa) => s + (wa.grammar_avg || 0), 0) + behavioralAreas.reduce((s, wa) => s + (wa.grammar_avg || 0), 0)) / (weakAreas.length)),
    };
}

/** Render a sorted list of dimension cards for a given scores object */
function DimensionList({ scores, isBehavioralOnly }) {
    const [expanded, setExpanded] = useState(null);

    // Filter dimensions: exclude semantic & keyword for behavioral-only topics
    const visibleDimensions = DIMENSIONS.filter(dim => {
        if (isBehavioralOnly && dim.behavioralExclude) return false;
        return true;
    });

    const sorted = [...visibleDimensions].sort((a, b) => (scores[a.key] || 0) - (scores[b.key] || 0));

    return (
        <div className="wa-list">
            {sorted.map(dim => {
                const score = Math.round((scores[dim.key] || 0) * 100) / 100;
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
    );
}

export default function WeakAreas() {
    const navigate = useNavigate();
    const [weakAreas, setWeakAreas] = useState([]);   // raw rows from user_weak_areas
    const [sessionCount, setSessionCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState("overall");
    const userId = getUserId();

    useEffect(() => { fetchData(); }, []);

    const fetchData = async () => {
        try {
            const [waRes, sessRes] = await Promise.all([
                axios.get(`${BASE_URL}/weak-areas/user/${userId}`),
                axios.get(`${BASE_URL}/sessions/user/${userId}/history`),
            ]);
            setWeakAreas(waRes.data);
            setSessionCount(sessRes.data.filter(s => s.completed).length);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return (
        <div className="app-layout">
            <Sidebar />
            <div className="wa-wrapper wa-center"><p className="loading-text">⏳ Analysing your scores…</p></div>
        </div>
    );

    const overallScores = buildOverall(weakAreas);

    // Active topic row (null when "overall" tab selected)
    const activeTopicRow = activeTab === "overall"
        ? null
        : weakAreas.find(wa => wa.topic === activeTab);

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
                ) : !overallScores ? (
                    <div className="wa-empty">
                        <p>Skill data is being processed. Complete a full interview session (all 5 questions) to see your breakdown.</p>
                    </div>
                ) : (
                    <>
                        {/* ── Tab bar ── */}
                        <div className="wa-tabs">
                            <button
                                className={`wa-tab ${activeTab === "overall" ? "wa-tab--active" : ""}`}
                                onClick={() => setActiveTab("overall")}
                            >
                                Overall
                            </button>
                            {weakAreas.map(wa => {
                                const ovr = topicOverallScore(wa);
                                const style = getScoreColor(ovr);
                                return (
                                    <button
                                        key={wa.topic}
                                        className={`wa-tab ${activeTab === wa.topic ? "wa-tab--active" : ""}`}
                                        onClick={() => setActiveTab(wa.topic)}
                                    >
                                        {wa.topic}
                                        <span
                                            className="wa-tab-badge"
                                            style={{ background: style.color }}
                                        >
                                            {ovr}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>

                        {/* ── Topic meta (shown when a topic tab is active) ── */}
                        {activeTopicRow && (
                            <div className="wa-topic-meta">
                                <span className="wa-topic-meta-label">Topic</span>
                                <span className="wa-topic-meta-name">{activeTopicRow.topic}</span>
                                <span className="wa-topic-meta-sep">·</span>
                                <span className="wa-topic-meta-attempts">
                                    {activeTopicRow.attempt_count} question{activeTopicRow.attempt_count !== 1 ? "s" : ""} attempted
                                </span>
                                {activeTopicRow.role && (
                                    <>
                                        <span className="wa-topic-meta-sep">·</span>
                                        <span className="wa-topic-meta-role">{activeTopicRow.role}</span>
                                    </>
                                )}
                            </div>
                        )}

                        {/* ── Dimension cards ── */}
                        <DimensionList
                            scores={activeTab === "overall" ? overallScores : activeTopicRow}
                            isBehavioralOnly={activeTab === "overall" ? false : activeTopicRow?.is_behavioral_only}
                        />
                    </>
                )}
            </div>
        </div>
    );
}

