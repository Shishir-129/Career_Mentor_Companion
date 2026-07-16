import Sidebar from "../components/Sidebar";
import { getAuth } from "../api/config";
import "./Settings.css";

export default function Settings() {
    const auth = getAuth();

    return (
        <div className="app-layout">
            <Sidebar />
            <div className="settings-wrapper">
                <h1 className="settings-title">Account</h1>
                <p className="settings-subtitle">Your profile information</p>

                <div className="settings-form">
                    <div className="settings-field">
                        <span className="settings-label">Full Name</span>
                        <span className="settings-value">{auth?.fullname}</span>
                    </div>
                    <div className="settings-field">
                        <span className="settings-label">Email</span>
                        <span className="settings-value">{auth?.email}</span>
                    </div>
                    <div className="settings-field">
                        <span className="settings-label">Target Role</span>
                        <span className="settings-value">{auth?.target_role}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
