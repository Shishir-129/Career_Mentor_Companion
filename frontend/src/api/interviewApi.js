import axios from "axios";
import { BASE_URL } from "./config";

// ── Auth ──────────────────────────────────────────────────────────────────────
export const loginUser = async (email, password) => {
    const res = await axios.post(`${BASE_URL}/users/login`, { email, password });
    return res.data;
};

export const registerUser = async (fullname, email, password, target_role) => {
    const res = await axios.post(`${BASE_URL}/users/register`, {
        fullname, email, password, target_role,
    });
    return res.data;
};

// ── Sessions ──────────────────────────────────────────────────────────────────
export const createSession = async (userId, role) => {
    const res = await axios.post(`${BASE_URL}/sessions/`, {
        user_id: userId,
        role: role,
    });
    return res.data;
};

// POST /questions/for-session — fetch questions matching role + level + difficulty
export const getQuestionsForSession = async (role, level, interviewType, difficulty, count = 5) => {
    const res = await axios.post(`${BASE_URL}/questions/for-session`, {
        role,
        level,
        interview_type: interviewType,
        difficulty,
        count,
    });
    return res.data;
};

// POST /responses/upload-audio — submit recorded audio answer
export const submitAudioResponse = async ({ sessionId, userId, questionId, questionType, topic, audioBlob }) => {
    const formData = new FormData();
    formData.append("session_id", sessionId);
    formData.append("user_id", userId);
    formData.append("question_id", questionId);
    if (questionType) formData.append("question_type", questionType);
    if (topic) formData.append("topic", topic);

    // ✅ Determine file extension based on actual blob MIME type
    const mimeType = audioBlob.type || "audio/webm";
    let ext = "wav"; // default
    if (mimeType.includes("mp4") || mimeType.includes("mpeg")) ext = "mp4";
    else if (mimeType.includes("ogg")) ext = "ogg";
    else if (mimeType.includes("webm")) ext = "webm";
    
    const filename = `answer.${ext}`;
    console.log(`📨 Uploading audio as ${filename} (type: ${mimeType}, size: ${audioBlob.size} bytes)`);
    formData.append("audio_file", audioBlob, filename);

    const res = await axios.post(`${BASE_URL}/responses/upload-audio`, formData, {
        timeout: 180000,  // 180 seconds (3 minutes) - scoring + FLAN-T5 can take time
        // ✅ DO NOT set Content-Type — axios auto-detects FormData and sets boundary
    });
    return res.data;
};

// ✅ PATCH /sessions/{session_id}/end — mark session as completed
export const completeSession = async (sessionId) => {
    try {
        const res = await axios.patch(
            `${BASE_URL}/sessions/${sessionId}/end`,
            {
                total_questions: 5,
                answered: 5,
                completed: true,
            }
        );
        return res.data;
    } catch (err) {
        console.error("Error completing session:", err);
        throw err;
    }
};

// ── Adaptive scoring / human-in-the-loop review ─────────────────────────────
// GET /responses/user/{user_id} — all responses (with scores) for review/labeling
export const getResponsesByUser = async (userId) => {
    const res = await axios.get(`${BASE_URL}/responses/user/${userId}`);
    return res.data;
};

// PATCH /responses/{response_id}/human-feedback — save a reviewer's ground-truth score (0–100)
export const submitHumanFeedback = async (responseId, actualScore) => {
    const res = await axios.patch(`${BASE_URL}/responses/${responseId}/human-feedback`, {
        actual_score: actualScore,
    });
    return res.data;
};

// POST /responses/retrain-model — retrain the adaptive model on all labeled responses
export const retrainScoringModel = async () => {
    const res = await axios.post(`${BASE_URL}/responses/retrain-model`);
    return res.data;
};