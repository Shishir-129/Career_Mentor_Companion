// frontend/src/api/interviewApi.js
import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000";

// POST /sessions/ — create a new interview session
export const createSession = async (userId, role) => {
    const res = await axios.post(`${BASE_URL}/sessions/`, {
        user_id: userId,
        role: role,
    });
    return res.data;
};

// POST /questions/for-session — fetch questions matching role + level
export const getQuestionsForSession = async (role, level, interviewType, count = 5) => {
    const res = await axios.post(`${BASE_URL}/questions/for-session`, {
        role: role,
        level: level,
        interview_type: interviewType,
        count: count,
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