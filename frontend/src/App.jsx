import { Routes, Route, Navigate } from "react-router-dom";
import { getAuth } from "./api/config";
import Login from "./pages/Login";
import NewInterview from "./pages/NewInterview";
import StartInterview from "./pages/StartInterview";
import Dashboard from "./pages/Dashboard";
import Settings from "./pages/Settings";
import WeakAreas from "./pages/WeakAreas";

function RequireAuth({ children }) {
    return getAuth() ? children : <Navigate to="/login" replace />;
}

export default function App() {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
            <Route path="/new-interview" element={<RequireAuth><NewInterview /></RequireAuth>} />
            <Route path="/interview" element={<RequireAuth><StartInterview /></RequireAuth>} />
            <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
            <Route path="/weak-areas" element={<RequireAuth><WeakAreas /></RequireAuth>} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
    );
}
