import { NavLink } from "react-router-dom";
import './Sidebar.css';
import { CURRENT_USER } from "../config/user";

import {
    FiGrid,
    FiPlus,
    FiClock,
    FiBarChart2,
    FiAlertCircle,
    FiSettings
} from 'react-icons/fi';

export default function Sidebar() {
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

                <NavLink
                    to="/new-interview"
                    className="nav-item"
                >
                    <FiPlus />
                    New Interview
                </NavLink>

                <NavLink
                    to="/history"
                    className="nav-item"
                >
                    <FiClock />
                    History
                </NavLink>

                <NavLink
                    to="/analytics"
                    className="nav-item"
                >
                    <FiBarChart2 />
                    Analytics
                </NavLink>

                <NavLink
                    to="/weak-areas"
                    className="nav-item"
                >
                    <FiAlertCircle />
                    Weak Areas
                </NavLink>

                <NavLink
                    to="/settings"
                    className="nav-item"
                >
                    <FiSettings />
                    Settings
                </NavLink>
            </nav>

            <div className="user-card">
                <div className="avatar">{CURRENT_USER.initials}</div>

                <div>
                    <strong>{CURRENT_USER.name}</strong>
                    <p>{CURRENT_USER.role}</p>
                </div>
            </div>

        </aside>
    )
}