import { Routes, Route, Navigate } from "react-router-dom";
import NewInterview from "./pages/NewInterview";
import StartInterview from "./pages/StartInterview";

export default function App() {
  return (
    <Routes>
        <Route path="/" element={<Navigate to="/new-interview" replace />} />
        <Route path="/new-interview" element={<NewInterview />} />
        <Route path="/interview" element={<StartInterview />} />
    </Routes>
  );
}