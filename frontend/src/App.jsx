import { Routes, Route } from "react-router-dom";
import NewInterview from "./pages/NewInterview";


export default function App() {
  return (
    <Routes>
        <Route path="/new-interview" element={<NewInterview />} />
    </Routes>
  );
}