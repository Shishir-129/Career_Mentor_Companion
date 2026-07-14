// frontend/src/pages/WeakAreas.jsx
import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import axios from "axios";
import { FiAlertCircle, FiBarChart2, FiCheckCircle } from "react-icons/fi";
import "./WeakAreas.css";

const BASE_URL = "http://127.0.0.1:8000";

export default function WeakAreas() {
    const [weakAreas, setWeakAreas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const userId = 1;

    useEffect(() => {
        fetchWeakAreas();
    }, []);

    const fetchWeakAreas = async () => {
        try {
            setLoading(true);
            const res = await axios.get(
                `${BASE_URL}/weak-areas/user/${userId}`
            );
            // Filter areas with avg_score < 75 as "weak"
            const weak = res.data.filter(area => area.avg_score < 75);
            setWeakAreas(weak);
            setError(null);
        } catch (err) {
            console.error("Error fetching weak areas:", err);
            setError("Failed to load weak areas data");
        } finally {
            setLoading(false);
        }
    };

    const getPriorityLevel = (score) => {
        if (score < 60) return "High Priority";
        if (score < 75) return "Medium Priority";
        return "Low Priority";
    };

    const getPriorityColor = (priority) => {
        if (priority === "High Priority") return "#ef4444";
        if (priority === "Medium Priority") return "#f97316";
        return "#eab308";
    };

    const getImprovementTips = (topic) => {
        const tips = {
            "System Design": [
                "Study scalability patterns",
                "Learn about load balancing",
                "Practice designing real-world systems"
            ],
            "Coding": [
                "Practice algorithm problems",
                "Focus on time complexity",
                "Work on clean code practices"
            ],
            "Data Structures": [
                "Master hash tables",
                "Learn tree/graph operations",
                "Practice problem solving"
            ],
            "Database": [
                "Study normalization",
                "Learn indexing strategies",
                "Practice query optimization"
            ],
        };
        return tips[topic] || [
            "Practice more questions on this topic",
            "Review fundamental concepts",
            "Study industry best practices"
        ];
    };

    if (loading) {
        return (
            <div className="app-layout">
                <Sidebar />
                <div className="weak-areas-wrapper weak-areas-center">
                    <p className="loading-text">⏳ Loading weak areas...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="app-layout">
                <Sidebar />
                <div className="weak-areas-wrapper weak-areas-center">
                    <p className="error-text">{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="app-layout">
            <Sidebar />
            <div className="weak-areas-wrapper">
                {/* Header */}
                <div className="weak-areas-header">
                    <div>
                        <h1 className="weak-areas-title">Weak Areas</h1>
                        <p className="weak-areas-subtitle">
                            Focused improvement opportunities based on your performance.
                        </p>
                    </div>
                </div>

                {/* Weak Areas Cards */}
                {weakAreas.length === 0 ? (
                    <div className="empty-state">
                        <p className="empty-icon">🎉</p>
                        <p className="empty-text">No weak areas detected!</p>
                        <p className="empty-subtext">Keep practicing to maintain your performance.</p>
                    </div>
                ) : (
                    <div className="weak-areas-grid">
                        {weakAreas.map((area, idx) => (
                            <WeakAreaCard
                                key={idx}
                                area={area}
                                priority={getPriorityLevel(area.avg_score)}
                                priorityColor={getPriorityColor(
                                    getPriorityLevel(area.avg_score)
                                )}
                                tips={getImprovementTips(area.topic)}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function WeakAreaCard({ area, priority, priorityColor, tips }) {
    const targetScore = 85;
    const progressPercent = (area.avg_score / targetScore) * 100;

    return (
        <div className="weak-area-card">
            {/* Card Header */}
            <div className="weak-area-header">
                <div className="weak-area-title-section">
                    <div className="weak-area-icon">
                        <FiAlertCircle style={{ color: priorityColor }} />
                    </div>
                    <div>
                        <h3 className="weak-area-name">{area.topic}</h3>
                        <p className="weak-area-meta">
                            {area.role} • {area.question_type}
                        </p>
                        <span 
                            className="priority-badge"
                            style={{ 
                                backgroundColor: `${priorityColor}20`,
                                color: priorityColor
                            }}
                        >
                            {priority}
                        </span>
                    </div>
                </div>
                <div className="weak-area-score">
                    <span className="score-value" style={{ color: priorityColor }}>
                        {Math.round(area.avg_score)}
                    </span>
                    <span className="score-max">/100</span>
                </div>
            </div>

            {/* Progress Bar */}
            <div className="progress-section">
                <div className="progress-info">
                    <span className="progress-label">Current: {Math.round(area.avg_score)}</span>
                    <span className="progress-label">Target: {targetScore}+</span>
                </div>
                <div className="progress-bar">
                    <div
                        className="progress-fill"
                        style={{
                            width: `${Math.min(progressPercent, 100)}%`,
                            backgroundColor: priorityColor,
                        }}
                    />
                </div>
            </div>

            {/* Attempts Count */}
            <div className="attempts-section">
                <FiBarChart2 style={{ color: "#666" }} />
                <span className="attempts-text">
                    {area.attempt_count} attempt{area.attempt_count !== 1 ? 's' : ''} on this topic
                </span>
            </div>

            {/* Improvement Tips */}
            <div className="improvement-section">
                <h4 className="improvement-title">💡 Improvement Tips</h4>
                <ul className="tips-list">
                    {tips.map((tip, idx) => (
                        <li key={idx} className="tip-item">
                            <span className="tip-icon">✓</span>
                            <span className="tip-text">{tip}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}