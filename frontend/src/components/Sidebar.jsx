import { NavLink, useNavigate } from "react-router-dom";
import './Sidebar.css';
import { getAuth, clearAuth } from "../api/config";

import {
    FiGrid,
    FiPlus,
    FiAlertCircle,
    FiSettings,
    FiLogOut,
    FiCheckSquare,
} from 'react-icons/fi';

export default function Sidebar() {
    const navigate = useNavigate();
    const auth = getAuth();
    const initials = auth?.fullname
        ?.split(" ")
        .map(n => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2) || "?";

    const handleLogout = () => {
        clearAuth();
        navigate("/login", { replace: true });
    };

    return (
        <aside className='sidebar'>
            <div className="logo">
                <div className="logo-circle">🎤</div>
                <div>
                    <h2>InterviewAI</h2>
                    <p>Coach Platform</p>
                </div>
            </div>

            <nav>
                <NavLink to='/dashboard' className='nav-item'>
                    <FiGrid /> Dashboard
                </NavLink>
                <NavLink to="/new-interview" className="nav-item">
                    <FiPlus /> New Interview
                </NavLink>
                <NavLink to="/weak-areas" className="nav-item">
                    <FiAlertCircle /> Weak Areas
                </NavLink>
                <NavLink to="/review-train" className="nav-item">
                    <FiCheckSquare /> Review &amp; Train
                </NavLink>
                <NavLink to="/settings" className="nav-item">
                    <FiSettings /> Settings
                </NavLink>
            </nav>

            <div className="sidebar-bottom">
                <div className="user-card">
                    <div className="avatar">{initials}</div>
                    <div className="user-info">
                        <strong>{auth?.fullname || "Guest"}</strong>
                        <p>{auth?.target_role || ""}</p>
                    </div>
                </div>
                <button className="logout-btn" onClick={handleLogout}>
                    <FiLogOut /> Sign out
                </button>
            </div>
        </aside>
    );
}
