import { useState } from "react";
import Sidebar from "../components/Sidebar";
import { CURRENT_USER, saveUser } from "../config/user";
import "./Settings.css";

export default function Settings() {
    const [name, setName] = useState(CURRENT_USER.name);
    const [initials, setInitials] = useState(CURRENT_USER.initials);
    const [role, setRole] = useState(CURRENT_USER.role);

    const handleSave = (e) => {
        e.preventDefault();
        saveUser({ name, initials, role });
        window.location.reload();
    };

    return (
        <div className="app-layout">
            <Sidebar />
            <div className="settings-wrapper">
                <h1 className="settings-title">Settings</h1>
                <p className="settings-subtitle">Update your profile info</p>

                <form onSubmit={handleSave} className="settings-form">
                    <label>
                        Name
                        <input
                            type="text"
                            className="settings-input"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                        />
                    </label>

                    <label>
                        Initials
                        <input
                            type="text"
                            className="settings-input"
                            value={initials}
                            onChange={(e) => setInitials(e.target.value)}
                            maxLength={2}
                        />
                    </label>

                    <label>
                        Role
                        <input
                            type="text"
                            className="settings-input"
                            value={role}
                            onChange={(e) => setRole(e.target.value)}
                        />
                    </label>

                    <button type="submit" className="btn-large">
                        Save
                    </button>
                </form>
            </div>
        </div>
    );
}