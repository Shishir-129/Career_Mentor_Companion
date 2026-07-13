import Sidebar from "../components/Sidebar";
import { useState } from "react";
import "./NewInterview.css";
import {
    FiCode,
    FiBarChart2,
    FiLayers,
    FiFeather,
    FiActivity,
    FiGlobe,
    FiBookOpen,
    FiPlay,
    FiChevronDown,
} from "react-icons/fi";

const JOB_ROLES = [
    { id: "data-analyst", label: "Data Analyst", icon: FiCode },
    { id: "data-scientist", label: "Data Scientist", icon: FiGlobe },
    { id: "devops-engineer", label: "Devops Enginner", icon: FiActivity }
];

const EXPERIENCE_LEVELS = ["0-2 Years", "3-5 Years", "6-8 Years", "9+ Years"];
const DIFFICULTIES = ["Easy", "Medium", "Hard"];
const INTERVIEW_TYPES = ["Technical", "Behavioral", "System Design", "Mixed"];


export default function NewInterview() {
    const [role, setRole] = useState(null);
    const [experience, setExperience] = useState("3-5 Years");
    const [difficulty, setDifficulty] = useState("Medium");
    const [interviewType, setInterviewType] = useState("Technical");

    const canStart = Boolean(role);

    return (
        <div className="app-layout">
            <Sidebar />
            <div className="main-content">
                <div className="new-interview">
                    <h1>Configure Your Interview</h1>
                    <p className="subtitle">
                        Set up a mock interview tailored to your target role and level.
                    </p>

                    <section>
                        <h3 className="section-label">Job Role</h3>
                        <div className="role-grid">
                            {JOB_ROLES.map(({ id, label, icon: Icon }) => (
                                <button
                                    key={id}
                                    type="button"
                                    className={`role-card ${role === id ? "selected" : ""}`}
                                    onClick={() => setRole(id)}
                                >
                                    <span className="role-icon">
                                        <Icon />
                                    </span>
                                    <span>{label}</span>
                                </button>
                            ))}
                        </div>
                    </section>

                    <div className="config-row">
                        <div className="config-col">
                            <h3 className="section-label">Experience Level</h3>
                            <div className="select-wrapper">
                                <select
                                    value={experience}
                                    onChange={(e) => setExperience(e.target.value)}
                                >
                                    {EXPERIENCE_LEVELS.map((level) => (
                                        <option key={level} value={level}>
                                            {level}
                                        </option>
                                    ))}
                                </select>
                                <FiChevronDown className="select-caret" />
                            </div>
                        </div>

                        <div className="config-col">
                            <h3 className="section-label">Difficulty</h3>
                            <div className="difficulty-group">
                                {DIFFICULTIES.map((level) => (
                                    <button
                                        key={level}
                                        type="button"
                                        className={`difficulty-btn ${difficulty === level ? "selected" : ""
                                            }`}
                                        onClick={() => setDifficulty(level)}
                                    >
                                        {level}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="config-col">
                            <h3 className="section-label">Interview Type</h3>
                            <div className="select-wrapper">
                                <select
                                    value={interviewType}
                                    onChange={(e) => setInterviewType(e.target.value)}
                                >
                                    {INTERVIEW_TYPES.map((type) => (
                                        <option key={type} value={type}>
                                            {type}
                                        </option>
                                    ))}
                                </select>
                                <FiChevronDown className="select-caret" />
                            </div>
                        </div>
                    </div>

                    <div className="session-preview">
                        <span className="preview-icon">
                            <FiBookOpen />
                        </span>
                        <p>
                            <strong>Session Preview:</strong> 5 questions &middot;{" "}
                            {interviewType} focus &middot; {difficulty} difficulty &middot;{" "}
                            {experience} level
                        </p>
                    </div>

                    <button
                        type="button"
                        className="start-btn"
                        disabled={!canStart}
                        onClick={() => {
                            if (canStart) {
                                // hook up navigation / session start here
                            }
                        }}
                    >
                        <FiPlay /> Start Interview
                    </button>

                    {!canStart && (
                        <p className="helper-text">Please select a job role to continue.</p>
                    )}
                </div>
            </div>
        </div>
    );
}
