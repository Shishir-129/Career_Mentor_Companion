// frontend/src/pages/Dashboard.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import axios from "axios";
import {
    LineChart, Line, ResponsiveContainer,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import { FiTrendingUp } from "react-icons/fi";
import "./Dashboard.css";
import { BASE_URL, getAuth, getUserId } from "../api/config";

export default function Dashboard() {
    const navigate = useNavigate();
    const auth = getAuth();
    const userId = getUserId();
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState("all");

    useEffect(() => { fetchSessions(); }, []);

    const fetchSessions = async () => {
        try {
            setLoading(true);
            const res = await axios.get(`${BASE_URL}/sessions/user/${userId}/history`);
            setSessions(res.data);
            setError(null);
        } catch (err) {
            console.error(err);
            setError("Failed to load dashboard data");
        } finally {
            setLoading(false);
        }
    };

    const completed = sessions.filter(s => s.completed);
    const abandoned = sessions.filter(s => !s.completed);

    const avg = (arr) => arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : 0;

    const stats = {
        completedCount: completed.length,
        abandonedCount: abandoned.length,
        avgScore: avg(completed.map(s => s.overall_score || 0)),
        bestScore: completed.length ? Math.round(Math.max(...completed.map(s => s.overall_score || 0))) : 0,
        avgAnswerQuality: avg(completed.map(s => s.scores?.answer_quality_avg || 0)),
        avgConfidence: avg(completed.map(s => s.scores?.confidence_avg || 0)),
    };

    const trendData = completed.slice(0, 8).reverse().map((s, i) => ({
        session: `#${i + 1}`,
        quality: Math.round(s.scores?.answer_quality_avg || 0),
        confidence: Math.round(s.scores?.confidence_avg || 0),
    }));

    const filteredSessions =
        filter === "completed" ? completed :
        filter === "abandoned" ? abandoned :
        sessions;

    const firstName = auth?.fullname?.split(" ")[0] || "there";

    if (loading) return (
        <div className="app-layout">
            <Sidebar />
            <div className="dash-wrapper dash-center"><p className="loading-text">⏳ Loading dashboard…</p></div>
        </div>
    );

    return (
        <div className="app-layout">
            <Sidebar />
            <div className="dash-wrapper">

                {/* Header */}
                <div className="dash-header">
                    <div>
                        <h1 className="dash-greeting">Welcome back, {firstName}</h1>
                        <p className="dash-sub">
                            {stats.completedCount === 0
                                ? "Start your first interview to see your progress here."
                                : `${stats.completedCount} completed session${stats.completedCount !== 1 ? "s" : ""} • ${sessions.length} total`}
                        </p>
                    </div>
                    <button className="btn-primary" onClick={() => navigate("/new-interview")}>
                        + New Interview
                    </button>
                </div>

                {/* Stats */}
                <div className="dash-stats">
                    <StatCard label="Completed" value={stats.completedCount} />
                    <StatCard label="Avg Score" value={stats.avgScore} suffix="/100" />
                    <StatCard label="Best Score" value={stats.bestScore} suffix="/100" highlight />
                    <StatCard label="Avg Answer Quality" value={stats.avgAnswerQuality} suffix="/100" />
                    <StatCard label="Avg Confidence" value={stats.avgConfidence} suffix="/100" />
                </div>

                {/* Trend chart */}
                {trendData.length >= 2 && (
                    <div className="dash-card">
                        <div className="dash-card-header">
                            <h3><FiTrendingUp /> Performance Trend</h3>
                            <span className="dash-card-sub">last {trendData.length} sessions</span>
                        </div>
                        <ResponsiveContainer width="100%" height={240}>
                            <LineChart data={trendData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                <XAxis dataKey="session" stroke="#bbb" tick={{ fontSize: 12 }} />
                                <YAxis domain={[0, 100]} stroke="#bbb" tick={{ fontSize: 12 }} />
                                <Tooltip contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "13px" }} />
                                <Legend wrapperStyle={{ fontSize: "13px" }} />
                                <Line type="monotone" dataKey="quality" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} name="Answer Quality" />
                                <Line type="monotone" dataKey="confidence" stroke="#7c3aed" strokeWidth={2} dot={{ r: 3 }} name="Confidence" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Recent Sessions */}
                <div className="dash-card">
                    <div className="dash-card-header">
                        <div>
                            <h3>Recent Sessions</h3>
                            <p className="dash-card-sub">{sessions.length} total sessions</p>
                        </div>
                        <div className="dash-filters">
                            {[["all", sessions.length], ["completed", stats.completedCount], ["abandoned", stats.abandonedCount]].map(([key, count]) => (
                                <button key={key} className={`filter-btn ${filter === key ? "active" : ""}`} onClick={() => setFilter(key)}>
                                    {key.charAt(0).toUpperCase() + key.slice(1)} ({count})
                                </button>
                            ))}
                        </div>
                    </div>

                    {error && <p style={{ color: "#ef4444", padding: "1rem 0" }}>{error}</p>}

                    {filteredSessions.length === 0 ? (
                        <div className="dash-empty">
                            <p>
                                {filter === "all"
                                    ? "No interviews yet."
                                    : `No ${filter} interviews.`}
                            </p>
                            <button className="btn-secondary" onClick={() => navigate("/new-interview")}>
                                Start Interview
                            </button>
                        </div>
                    ) : (
                        <div className="session-list">
                            {filteredSessions.map(s => <SessionRow key={s.session_id} session={s} />)}
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
}

function StatCard({ label, value, suffix = "", highlight = false }) {
    return (
        <div className={`stat-card ${highlight ? "highlight" : ""}`}>
            <p className="stat-label">{label}</p>
            <p className="stat-value">{value}<span className="stat-suffix">{suffix}</span></p>
        </div>
    );
}

function SessionRow({ session }) {
    const score = Math.round(session.overall_score || 0);
    const color = score >= 70 ? "#22c55e" : score >= 45 ? "#f59e0b" : "#ef4444";

    const date = new Date(session.started_at).toLocaleDateString("en-US", {
        month: "short", day: "numeric", year: "numeric",
    });

    return (
        <div className="session-row">
            <div className="session-score" style={{ color }}>{score}</div>
            <div className="session-info">
                <span className="session-role">{session.role}</span>
                <span className="session-date">{date} • {session.answered}/{session.total_questions} Q answered</span>
            </div>
            <div className="session-scores">
                <ScoreChip label="Answer Quality" value={Math.round(session.scores?.answer_quality_avg || 0)} />
                <ScoreChip label="Confidence" value={Math.round(session.scores?.confidence_avg || 0)} />
            </div>
            <span className={`status-badge ${session.completed ? "completed" : "abandoned"}`}>
                {session.completed ? "Completed" : "Abandoned"}
            </span>
        </div>
    );
}

function ScoreChip({ label, value }) {
    return (
        <div className="score-chip">
            <span className="chip-value">{value}</span>
            <span className="chip-label">{label}</span>
        </div>
    );
}
