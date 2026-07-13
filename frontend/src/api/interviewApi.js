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

    // Detect the actual MIME type and use the correct file extension
    // Browser MediaRecorder records as audio/webm (not wav), so sending as .wav causes 500
    const mimeType = audioBlob.type || "audio/webm";
    const ext = mimeType.includes("wav") ? "wav"
              : mimeType.includes("ogg") ? "ogg"
              : mimeType.includes("mp4") ? "mp4"
              : "webm";
    formData.append("audio_file", audioBlob, `answer.${ext}`);

    const res = await axios.post(`${BASE_URL}/responses/upload-audio`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
};