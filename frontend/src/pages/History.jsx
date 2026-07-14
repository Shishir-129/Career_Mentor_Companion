// frontend/src/pages/History.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import axios from "axios";
import "./History.css";

const BASE_URL = "http://127.0.0.1:8000";

export default function History() {
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
            setError("Failed to load interview history");
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

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    };

    const getScoreColor = (scoreValue) => {
        if (scoreValue >= 70) return "#4ade80";
        if (scoreValue >= 40) return "#facc15";
        return "#f87171";
    };

    const getScorePercentage = (score) => {
        return Math.round(score * 100) / 100;
    };

    const completedCount = sessions.filter(s => s.completed).length;
    const abandonedCount = sessions.filter(s => !s.completed).length;

    if (loading) {
        return (
            <div className="app-layout">
                <Sidebar />
                <div className="history-wrapper history-center">
                    <p className="loading-text">⏳ Loading your interviews...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="app-layout">
                <Sidebar />
                <div className="history-wrapper history-center">
                    <p className="error-text">{error}</p>
                    <button className="btn-primary" onClick={fetchSessions}>
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    const filteredSessions = getFilteredSessions();

    return (
        <div className="app-layout">
            <Sidebar />
            <div className="history-wrapper">
                {/* Header */}
                <div className="history-header">
                    <div className="history-title-section">
                        <h1>Interview History</h1>
                        <p className="history-subtitle">
                            {sessions.length} total sessions recorded
                        </p>
                    </div>
                    <button
                        className="btn-primary"
                        onClick={() => navigate("/new-interview")}
                    >
                        + New Interview
                    </button>
                </div>

                {/* Stats Bar */}
                <div className="history-stats">
                    <div className="stat-item">
                        <span className="stat-value">{sessions.length}</span>
                        <span className="stat-label">Total Sessions</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value">{completedCount}</span>
                        <span className="stat-label">Completed</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value">{abandonedCount}</span>
                        <span className="stat-label">Abandoned</span>
                    </div>
                </div>

                {/* Filters */}
                <div className="history-filters">
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
                        ✅ Completed ({completedCount})
                    </button>
                    <button
                        className={`filter-btn ${filter === "abandoned" ? "active" : ""}`}
                        onClick={() => setFilter("abandoned")}
                    >
                        ⏸ Abandoned ({abandonedCount})
                    </button>
                </div>

                {/* Sessions List */}
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
                                formatDate={formatDate}
                                getScoreColor={getScoreColor}
                                getScorePercentage={getScorePercentage}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function SessionListItem({
    session,
    formatDate,
    getScoreColor,
    getScorePercentage,
}) {
    const scoreColor = getScoreColor(session.overall_score);
    const scorePct = getScorePercentage(session.overall_score);

    return (
        <div className="session-list-item">
            {/* Score Circle */}
            <div className="session-score-circle" style={{ color: scoreColor }}>
                <div className="session-score-value">{scorePct}</div>
            </div>

            {/* Session Info */}
            <div className="session-list-info">
                <h3 className="session-list-role">{session.role}</h3>
                <div className="session-list-meta">
                    <span>{session.scores.semantic_avg.toFixed(0)}%</span>
                    <span>•</span>
                    <span>{session.scores.keyword_avg.toFixed(0)}%</span>
                    <span>•</span>
                    <span>{formatDate(session.started_at)}</span>
                </div>
            </div>

            {/* Individual Scores */}
            <div className="session-list-scores">
                <div className="score-item">
                    <span className="score-value">{Math.round(session.scores.answer_quality_avg)}</span>
                    <span className="score-label">COMP</span>
                </div>
                <div className="score-item">
                    <span className="score-value">{Math.round(session.scores.semantic_avg)}</span>
                    <span className="score-label">KEYS</span>
                </div>
                <div className="score-item">
                    <span className="score-value">{Math.round(session.scores.keyword_avg)}</span>
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

            {/* Status */}
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