import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser, registerUser } from "../api/interviewApi";
import { setAuth } from "../api/config";
import "./Login.css";

const ROLES = ["Data Analyst", "Data Scientist", "DevOps Engineer"];

export default function Login() {
    const [tab, setTab] = useState("login");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const navigate = useNavigate();

    // Login state
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    // Register state
    const [fullname, setFullname] = useState("");
    const [regEmail, setRegEmail] = useState("");
    const [regPassword, setRegPassword] = useState("");
    const [targetRole, setTargetRole] = useState("Data Analyst");

    const switchTab = (t) => { setTab(t); setError(""); };

    const handleLogin = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const user = await loginUser(email, password);
            setAuth(user);
            navigate("/dashboard", { replace: true });
        } catch (err) {
            setError(err.response?.data?.detail || "Invalid email or password.");
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const user = await registerUser(fullname, regEmail, regPassword, targetRole);
            setAuth(user);
            navigate("/dashboard", { replace: true });
        } catch (err) {
            setError(err.response?.data?.detail || "Registration failed. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-card">
                <div className="login-logo">
                    <div className="login-logo-icon">🎤</div>
                    <div>
                        <h2 className="login-app-name">InterviewAI</h2>
                        <p className="login-app-sub">Your personal interview coach</p>
                    </div>
                </div>

                <div className="login-tabs">
                    <button className={`login-tab ${tab === "login" ? "active" : ""}`} onClick={() => switchTab("login")}>
                        Sign In
                    </button>
                    <button className={`login-tab ${tab === "register" ? "active" : ""}`} onClick={() => switchTab("register")}>
                        Create Account
                    </button>
                </div>

                {error && <p className="login-error">{error}</p>}

                {tab === "login" ? (
                    <form onSubmit={handleLogin} className="login-form">
                        <label>
                            Email
                            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                                placeholder="you@example.com" required disabled={loading} />
                        </label>
                        <label>
                            Password
                            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                                placeholder="••••••••" required disabled={loading} />
                        </label>
                        <button type="submit" className="login-btn" disabled={loading}>
                            {loading ? "Signing in…" : "Sign In"}
                        </button>
                    </form>
                ) : (
                    <form onSubmit={handleRegister} className="login-form">
                        <label>
                            Full Name
                            <input type="text" value={fullname} onChange={e => setFullname(e.target.value)}
                                placeholder="Jane Smith" required disabled={loading} />
                        </label>
                        <label>
                            Email
                            <input type="email" value={regEmail} onChange={e => setRegEmail(e.target.value)}
                                placeholder="you@example.com" required disabled={loading} />
                        </label>
                        <label>
                            Password
                            <input type="password" value={regPassword} onChange={e => setRegPassword(e.target.value)}
                                placeholder="Min. 6 characters" minLength={6} required disabled={loading} />
                        </label>
                        <label>
                            Target Role
                            <select value={targetRole} onChange={e => setTargetRole(e.target.value)} disabled={loading}>
                                {ROLES.map(r => <option key={r}>{r}</option>)}
                            </select>
                        </label>
                        <button type="submit" className="login-btn" disabled={loading}>
                            {loading ? "Creating account…" : "Create Account"}
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}
