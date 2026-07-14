// frontend/src/pages/Dashboard.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import axios from "axios";
import {
    LineChart,
    Line,
    ResponsiveContainer,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
} from "recharts";
import { FiTrendingUp, FiBarChart2, FiAward, FiZap } from "react-icons/fi";
import "./Dashboard.css";
import { CURRENT_USER } from "../config/user";

const BASE_URL = "http://127.0.0.1:8000";

export default function Dashboard() {
    const navigate = useNavigate();
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState("all");

    const userId = 1;

    useEffect(() => {
        fetchSessions();
    }, []);

    const fetchSessions = async () => {
        try {
            setLoading(true);
            const res = await axios.get(
                `${BASE_URL}/sessions/user/${userId}/history`
            );
            setSessions(res.data);
            setError(null);
        } catch (err) {
            console.error("Error fetching sessions:", err);
            setError("Failed to load dashboard data");
        } finally {
            setLoading(false);
        }
    };

    const getFilteredSessions = () => {
        if (filter === "completed") {
            return sessions.filter(s => s.completed);
        } else if (filter === "abandoned") {
            return sessions.filter(s => !s.completed);
        }
        return sessions;
    };

    const calculateStats = () => {
        const completedSessions = sessions.filter(s => s.completed);
        const completedCount = completedSessions.length;
        const abandonedCount = sessions.length - completedCount;

        if (completedCount === 0) {
            return {
                completedCount: 0,
                abandonedCount,
                averageScore: 0,
                bestScore: 0,
                averageConfidence: 0,
                averageKeyword: 0,
                averageCompleteness: 0,
                averageGrammar: 0,
                questionsAnswered: 0,
                averageResponseTime: 0,
            };
        }

        const scores = completedSessions.map(s => s.overall_score || 0);
        const confidenceScores = completedSessions.map(s => s.scores?.confidence_avg || 0);
        const keywordScores = completedSessions.map(s => s.scores?.keyword_avg || 0);
        const completenessScores = completedSessions.map(s => s.scores?.completeness_avg || 0);
        const grammarScores = completedSessions.map(s => s.scores?.grammatical_avg || 0);

        return {
            completedCount,
            abandonedCount,
            averageScore: Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 100) / 100,
            bestScore: Math.round(Math.max(...scores) * 100) / 100,
            averageConfidence: Math.round((confidenceScores.reduce((a, b) => a + b, 0) / confidenceScores.length) * 100) / 100,
            averageKeyword: Math.round((keywordScores.reduce((a, b) => a + b, 0) / keywordScores.length) * 100) / 100,
            averageCompleteness: Math.round((completenessScores.reduce((a, b) => a + b, 0) / completenessScores.length) * 100) / 100,
            averageGrammar: Math.round((grammarScores.reduce((a, b) => a + b, 0) / grammarScores.length) * 100) / 100,
            questionsAnswered: completedCount * 5,
            averageResponseTime: 88,
        };
    };

    const getPerformanceTrendData = () => {
        return sessions
            .filter(s => s.completed)
            .slice(0, 10)
            .map((session, idx) => ({
                date: `Session ${idx + 1}`,
                overall: session.overall_score || 0,
                confidence: session.scores?.confidence_avg || 0,
            }));
    };

    const getSkillsRadarData = () => {
        const stats = calculateStats();
        return [
            { skill: "Technical", value: Math.round(stats.averageScore) },
            { skill: "Fluency", value: Math.round(stats.averageGrammar) },
            { skill: "Communication", value: Math.round(stats.averageKeyword) },
            { skill: "Confidence", value: Math.round(stats.averageConfidence) },
            { skill: "Problem Solving", value: Math.round(stats.averageScore * 0.9) },
            { skill: "Vocabulary", value: Math.round(stats.averageCompleteness) },
        ];
    };

    const stats = calculateStats();
    const performanceTrendData = getPerformanceTrendData();
    const skillsRadarData = getSkillsRadarData();
    const filteredSessions = getFilteredSessions();

    if (loading) {
        return (
            <div className="app-layout">
                <Sidebar />
                <div className="dashboard-wrapper dashboard-center">
                    <p className="loading-text">⏳ Loading dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="app-layout">
            <Sidebar />
            <div className="dashboard-wrapper">
                {/* ── Greeting Section ── */}
                <div className="greeting-section">
                    <div className="greeting-content">
                        <h1 className="greeting-title">Good morning, {CURRENT_USER.name.split(" ")[0]}</h1>
                        <p className="greeting-subtitle">
                            Ready to improve your interview skills?
                        </p>
                    </div>
                    <button
                        className="btn-large"
                        onClick={() => navigate("/new-interview")}
                    >
                        + Start Interview
                    </button>
                </div>

                {/* ── Summary Stats ── */}
                <div className="summary-section">
                    <div className="summary-card">
                        <div className="summary-icon">📊</div>
                        <div className="summary-content">
                            <p className="summary-label">Overall Score</p>
                            <p className="summary-value">{stats.averageScore}</p>
                        </div>
                    </div>
                    <div className="summary-card">
                        <div className="summary-icon">🎤</div>
                        <div className="summary-content">
                            <p className="summary-label">Confidence Score</p>
                            <p className="summary-value">{stats.averageConfidence}</p>
                        </div>
                    </div>
                    <div className="summary-card">
                        <div className="summary-icon">🔑</div>
                        <div className="summary-content">
                            <p className="summary-label">Keyword Match</p>
                            <p className="summary-value">{stats.averageKeyword}</p>
                        </div>
                    </div>
                    <div className="summary-card">
                        <div className="summary-icon">✅</div>
                        <div className="summary-content">
                            <p className="summary-label">Completeness</p>
                            <p className="summary-value">{stats.averageCompleteness}</p>
                        </div>
                    </div>
                    <div className="summary-card">
                        <div className="summary-icon">❓</div>
                        <div className="summary-content">
                            <p className="summary-label">Questions Done</p>
                            <p className="summary-value">{stats.questionsAnswered}</p>
                        </div>
                    </div>
                    <div className="summary-card">
                        <div className="summary-icon">⏱️</div>
                        <div className="summary-content">
                            <p className="summary-label">Avg Response</p>
                            <p className="summary-value">{stats.averageResponseTime}s</p>
                        </div>
                    </div>
                </div>

                {/* ── Charts Section ── */}
                <div className="charts-section">
                    {/* Performance Trend */}
                    <div className="chart-card">
                        <div className="chart-header">
                            <h3 className="chart-title">
                                <FiTrendingUp /> Performance Trend
                            </h3>
                            <span className="chart-subtitle">Last 6 sessions</span>
                        </div>
                        {performanceTrendData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={performanceTrendData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                    <XAxis dataKey="date" stroke="#999" />
                                    <YAxis stroke="#999" />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: "#fff",
                                            border: "1px solid #e5e7eb",
                                            borderRadius: "0.5rem",
                                        }}
                                    />
                                    <Legend />
                                    <Line
                                        type="monotone"
                                        dataKey="overall"
                                        stroke="#2563eb"
                                        strokeWidth={2}
                                        dot={{ fill: "#2563eb", r: 4 }}
                                        activeDot={{ r: 6 }}
                                        name="Overall"
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="confidence"
                                        stroke="#8b5cf6"
                                        strokeWidth={2}
                                        dot={{ fill: "#8b5cf6", r: 4 }}
                                        activeDot={{ r: 6 }}
                                        name="Confidence"
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <p className="chart-empty">No data yet</p>
                        )}
                    </div>

                    {/* Skills Radar */}
                    <div className="chart-card">
                        <div className="chart-header">
                            <h3 className="chart-title">
                                <FiBarChart2 /> Skills Radar
                            </h3>
                        </div>
                        {skillsRadarData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={300}>
                                <RadarChart data={skillsRadarData}>
                                    <PolarGrid stroke="#e5e7eb" />
                                    <PolarAngleAxis dataKey="skill" stroke="#999" />
                                    <PolarRadiusAxis stroke="#999" />
                                    <Radar
                                        name="Skill Score"
                                        dataKey="value"
                                        stroke="#2563eb"
                                        fill="#2563eb"
                                        fillOpacity={0.6}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: "#fff",
                                            border: "1px solid #e5e7eb",
                                            borderRadius: "0.5rem",
                                        }}
                                    />
                                </RadarChart>
                            </ResponsiveContainer>
                        ) : (
                            <p className="chart-empty">No data yet</p>
                        )}
                    </div>
                </div>

                {/* ── History Section ── */}
                <div className="history-section">
                    <div className="history-header">
                        <div>
                            <h3 className="history-title">Recent Sessions</h3>
                            <p className="history-count">
                                {sessions.length} total sessions
                            </p>
                        </div>
                    </div>

                    <div className="dashboard-filters">
                        <button
                            className={`filter-btn ${filter === "all" ? "active" : ""}`}
                            onClick={() => setFilter("all")}
                        >
                            All ({sessions.length})
                        </button>
                        <button
                            className={`filter-btn ${filter === "completed" ? "active" : ""}`}
                            onClick={() => setFilter("completed")}
                        >
                            ✅ Completed ({stats.completedCount})
                        </button>
                        <button
                            className={`filter-btn ${filter === "abandoned" ? "active" : ""}`}
                            onClick={() => setFilter("abandoned")}
                        >
                            ⏸ Abandoned ({stats.abandonedCount})
                        </button>
                    </div>

                    {filteredSessions.length === 0 ? (
                        <div className="empty-state">
                            <p className="empty-icon">📭</p>
                            <p className="empty-text">
                                {filter === "all"
                                    ? "No interviews yet. Start your first interview!"
                                    : `No ${filter} interviews.`}
                            </p>
                            <button
                                className="btn-secondary"
                                onClick={() => navigate("/new-interview")}
                            >
                                Start Interview
                            </button>
                        </div>
                    ) : (
                        <div className="sessions-list">
                            {filteredSessions.map((session) => (
                                <SessionListItem
                                    key={session.session_id}
                                    session={session}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function SessionListItem({ session }) {
    const scoreColor =
        session.overall_score >= 70
            ? "#4ade80"
            : session.overall_score >= 40
            ? "#facc15"
            : "#f87171";

    const scorePct = Math.round(session.overall_score * 100) / 100;

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    };

    return (
        <div className="session-list-item">
            <div className="session-score-circle" style={{ color: scoreColor }}>
                <div className="session-score-value">{scorePct}</div>
            </div>

            <div className="session-list-info">
                <h3 className="session-list-role">{session.role}</h3>
                <div className="session-list-meta">
                    <span>{session.scores?.semantic_avg?.toFixed(0) || 0}%</span>
                    <span>•</span>
                    <span>{session.scores?.keyword_avg?.toFixed(0) || 0}%</span>
                    <span>•</span>
                    <span>{formatDate(session.started_at)}</span>
                </div>
            </div>

            <div className="session-list-scores">
                <div className="score-item">
                    <span className="score-value">
                        {Math.round(session.scores?.answer_quality_avg || 0)}
                    </span>
                    <span className="score-label">COMP</span>
                </div>
                <div className="score-item">
                    <span className="score-value">
                        {Math.round(session.scores?.semantic_avg || 0)}
                    </span>
                    <span className="score-label">KEYS</span>
                </div>
                <div className="score-item">
                    <span className="score-value">
                        {Math.round(session.scores?.keyword_avg || 0)}
                    </span>
                    <span className="score-label">COMP</span>
                </div>
                <div className="score-item">
                    <span className="score-value">5/10</span>
                    <span className="score-label">Q</span>
                </div>
                <div className="score-item">
                    <span className="score-value">88s</span>
                    <span className="score-label">TIME</span>
                </div>
            </div>

            <div className="session-status">
                {session.completed ? (
                    <span className="status-badge completed">✅ Completed</span>
                ) : (
                    <span className="status-badge abandoned">⏸ Abandoned</span>
                )}
            </div>
        </div>
    );
}