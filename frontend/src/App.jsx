import { Routes, Route, Navigate } from "react-router-dom";
import NewInterview from "./pages/NewInterview";
import StartInterview from "./pages/StartInterview";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import Settings from "./pages/Settings";
import WeakAreas from "./pages/WaakAreas";

export default function App() {
  return (
    <Routes>
        <Route path="/" element={<Navigate to="/new-interview" replace />} />
        <Route path="/new-interview" element={<NewInterview />} />
        <Route path="/interview" element={<StartInterview />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/history" element={<History />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/weak-areas" element={<WeakAreas />} />
    </Routes>
  );
}