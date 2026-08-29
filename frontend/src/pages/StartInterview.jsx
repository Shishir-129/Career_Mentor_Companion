// frontend/src/pages/StartInterview.jsx
import { useState, useRef, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { createSession, getQuestionsForSession, submitAudioResponse, completeSession, submitSessionRating } from "../api/interviewApi";
import { FiMic, FiSquare, FiChevronRight } from "react-icons/fi";
import "./StartInterview.css";
import { getUserId } from "../api/config";

export default function StartInterview() {
    const { state } = useLocation();
    const navigate = useNavigate();
    const { role, experience, difficulty, interviewType } = state || {};

    const [questions, setQuestions] = useState([]);
    const [sessionId, setSessionId] = useState(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loadingSession, setLoadingSession] = useState(true);
    const [error, setError] = useState(null);

    const [recording, setRecording] = useState(false);
    const [audioBlob, setAudioBlob] = useState(null);
    const [audioURL, setAudioURL] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [feedback, setFeedback] = useState(null);
    const [done, setDone] = useState(false);

    const [liveTranscript, setLiveTranscript] = useState("");
    const [finalTranscript, setFinalTranscript] = useState("");
    const [speechSupported, setSpeechSupported] = useState(true); // false when browser blocks Web Speech API
    const recognitionRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);

    const [timer, setTimer] = useState(0);
    const timerRef = useRef(null);
    const completedRef = useRef(false);

    const [rating, setRating] = useState(0);
    const [ratingSubmitted, setRatingSubmitted] = useState(false);

    const userId = getUserId();

    useEffect(() => {
        if (!role) { navigate("/new-interview"); return; }
        const init = async () => {
            try {
                const sessionData = await createSession(userId, role);
                setSessionId(sessionData.id);
                const questionsData = await getQuestionsForSession(
                    userId,
                    role,
                    experience,
                    interviewType,
                    difficulty,
                    5
                );
                setQuestions(questionsData);
            } catch (err) {
                console.error(err);
                setError("Failed to load questions. Is the backend running?");
            } finally {
                setLoadingSession(false);
            }
        };
        init();
    }, []);

    // Timer
    useEffect(() => {
        if (recording) {
            setTimer(0);
            timerRef.current = setInterval(() => setTimer(t => t + 1), 1000);
        } else {
            clearInterval(timerRef.current);
        }
        return () => clearInterval(timerRef.current);
    }, [recording]);

    // ✅ Mark session as completed when interview finishes
    useEffect(() => {
        const markComplete = async () => {
            if (sessionId && !completedRef.current) {
                try {
                    completedRef.current = true;
                    await completeSession(sessionId);
                } catch (err) {
                    console.error("Error marking session complete:", err);
                }
            }
        };

        if (done) {
            markComplete();
        }
    }, [done, sessionId]);

    const formatTime = (s) =>
        `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

    const handleRate = async (value) => {
        setRating(value);
        try {
            await submitSessionRating(sessionId, userId, value);
            setRatingSubmitted(true);
        } catch (err) {
            console.error("Error submitting rating:", err);
            alert("Could not save your rating. Please try again.");
        }
    };

    const currentQuestion = questions[currentIndex];

    const startRecording = async () => {
        setAudioBlob(null);
        setAudioURL(null);
        setFeedback(null);
        setLiveTranscript("");
        setFinalTranscript("");
        chunksRef.current = [];

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // ✅ Try to use WAV MIME type if available, fallback to WebM
            const mimeTypes = [
                "audio/wav",
                "audio/mp4",
                "audio/ogg",
                "audio/webm"
            ];
            let selectedMimeType = "audio/webm"; // default fallback
            for (const mimeType of mimeTypes) {
                if (MediaRecorder.isTypeSupported(mimeType)) {
                    selectedMimeType = mimeType;
                    if (mimeType.includes("wav") || mimeType.includes("mp4")) {
                        // Prefer WAV or MP4 over WebM
                        break;
                    }
                }
            }
            
            console.log(`📻 Recording with MIME type: ${selectedMimeType}`);
            const mediaRecorder = new MediaRecorder(stream, { mimeType: selectedMimeType });
            mediaRecorderRef.current = mediaRecorder;
            mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
            mediaRecorder.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: selectedMimeType });
                console.log(`💾 Recording complete: ${blob.size} bytes, type: ${blob.type}`);
                setAudioBlob(blob);
                setAudioURL(URL.createObjectURL(blob));
                stream.getTracks().forEach((t) => t.stop());
            };
            mediaRecorder.start();
            setRecording(true);
        } catch {
            alert("Microphone access denied. Please allow microphone.");
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            setSpeechSupported(false);
            return;
        }
        const recognition = new SpeechRecognition();
        recognition.lang = "en-US";
        recognition.continuous = true;
        recognition.interimResults = true;
        recognitionRef.current = recognition;
        recognition.onresult = (event) => {
            let interim = "";
            let final = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const t = event.results[i][0].transcript;
                if (event.results[i].isFinal) final += t + " ";
                else interim += t;
            }
            setFinalTranscript(prev => prev + final);
            setLiveTranscript(interim);
        };
        recognition.onerror = (e) => {
            // 'not-allowed' or 'service-not-allowed' means the browser blocked the API
            if (e.error === "not-allowed" || e.error === "service-not-allowed") {
                setSpeechSupported(false);
            }
        };
        try {
            recognition.start();
        } catch {
            setSpeechSupported(false);
        }
    };

    const stopRecording = () => {
        mediaRecorderRef.current?.stop();
        recognitionRef.current?.stop();
        setRecording(false);
        setLiveTranscript("");
    };

    const submitAnswer = async () => {
        if (!audioBlob) return;
        setSubmitting(true);
        try {
            console.log(`📤 Submitting audio: ${audioBlob.size} bytes, type: ${audioBlob.type}`);
            
            const result = await submitAudioResponse({
                sessionId, userId,
                questionId: currentQuestion.id,
                questionType: currentQuestion.question_type,
                topic: currentQuestion.topic,
                audioBlob,
            });
            setFeedback(result);
        } catch (err) {
            console.error("Submission error:", err);
            const errorMsg = err.response?.data?.detail || err.message || "Failed to submit answer. Please try again.";
            alert(errorMsg);
        } finally {
            setSubmitting(false);
        }
    };

    const nextQuestion = () => {
        if (currentIndex + 1 >= questions.length) {
            setDone(true);
        } else {
            setCurrentIndex(i => i + 1);
            setAudioBlob(null);
            setAudioURL(null);
            setFeedback(null);
            setLiveTranscript("");
            setFinalTranscript("");
            setTimer(0);
        }
    };

    if (loadingSession) return (
        <div className="app-layout"><Sidebar />
            <div className="si-wrapper si-center">
                <p className="loading-text">⏳ Setting up your interview...</p>
            </div>
        </div>
    );

    if (error) return (
        <div className="app-layout"><Sidebar />
            <div className="si-wrapper si-center">
                <p className="error-text">{error}</p>
                <button className="si-btn-primary" onClick={() => navigate("/new-interview")}>Go Back</button>
            </div>
        </div>
    );

    if (done) return (
        <div className="app-layout">
            <Sidebar />
            <div className="si-wrapper si-center">
                <div className="complete-card">
                    <h1 style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>
                        🎉 Session Complete!
                    </h1>
                    
                    <div style={{
                        background: "#f0f9ff",
                        border: "2px solid #bfdbfe",
                        borderRadius: "0.75rem",
                        padding: "1.5rem",
                        marginBottom: "1.5rem",
                        textAlign: "left",
                    }}>
                        <p style={{ margin: "0 0 0.5rem 0", fontSize: "0.95rem", color: "#666" }}>
                            <strong>Role:</strong> {role}
                        </p>
                        <p style={{ margin: "0 0 0.5rem 0", fontSize: "0.95rem", color: "#666" }}>
                            <strong>Questions Answered:</strong> {questions.length}
                        </p>
                        <p style={{ margin: "0", fontSize: "0.95rem", color: "#666" }}>
                            <strong>Interview Type:</strong> {interviewType}
                        </p>
                    </div>

                    <p style={{ fontSize: "1rem", color: "#333", marginBottom: "2rem" }}>
                        Great job! Your session has been saved to your dashboard.
                    </p>

                    <div style={{ marginBottom: "2rem" }}>
                        <p style={{ fontSize: "1rem", color: "#333", marginBottom: "0.75rem" }}>
                            How would you rate this session?
                        </p>
                        {ratingSubmitted ? (
                            <p style={{ color: "#16a34a", fontWeight: 600 }}>
                                ✅ Thanks for your feedback! You rated {rating}/5.
                            </p>
                        ) : (
                            <div style={{ display: "flex", gap: "0.5rem", justifyContent: "center" }}>
                                {[1, 2, 3, 4, 5].map((star) => (
                                    <button
                                        key={star}
                                        onClick={() => handleRate(star)}
                                        style={{
                                            background: "none",
                                            border: "none",
                                            cursor: "pointer",
                                            fontSize: "2rem",
                                            lineHeight: 1,
                                            color: star <= rating ? "#facc15" : "#d1d5db",
                                        }}
                                        aria-label={`Rate ${star} out of 5`}
                                    >
                                        ★
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    <div style={{
                        display: "flex",
                        gap: "1rem",
                        justifyContent: "center",
                        flexWrap: "wrap",
                    }}>
                        <button
                            className="si-btn-primary"
                            onClick={() => navigate("/dashboard")}
                            style={{
                                padding: "0.75rem 2rem",
                                fontSize: "1rem",
                            }}
                        >
                            📊 View Dashboard
                        </button>
                        <button
                            className="si-btn-secondary"
                            onClick={() => navigate("/new-interview")}
                            style={{
                                padding: "0.75rem 2rem",
                                fontSize: "1rem",
                                background: "#f3f4f6",
                                color: "#1a1a1a",
                                border: "2px solid #d1d5db",
                            }}
                        >
                            ➕ New Interview
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );

    return (
        <div className="app-layout">
            <Sidebar />
            <div className="si-wrapper">

                {/* Top bar */}
                <div className="si-topbar">
                    <span className="si-progress-label">
                        Question {currentIndex + 1} of {questions.length}
                    </span>
                    <div className="si-progress-track">
                        <div className="si-progress-fill"
                            style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }} />
                    </div>
                    <span className="si-timer">⏱ {formatTime(timer)}</span>
                </div>

                {/* Body */}
                <div className="si-body">

                    {/* LEFT */}
                    <div className="si-left">

                        {/* Session badges */}
                        <div className="si-badges">
                            <span className="si-badge">{role}</span>
                            <span className="si-badge secondary">{interviewType}</span>
                            <span className="si-badge secondary">{difficulty}</span>
                            <span className="si-badge secondary">{experience}</span>
                        </div>

                        {/* Question card */}
                        <div className="si-question-card">
                            <div className="si-question-tags">
                                {currentQuestion?.topic && <span className="si-tag">{currentQuestion.topic}</span>}
                                {currentQuestion?.question_type && <span className="si-tag">{currentQuestion.question_type}</span>}
                                {currentQuestion?.difficulty && <span className="si-tag">{currentQuestion.difficulty}</span>}
                                {currentQuestion?.experience_level && <span className="si-tag">{currentQuestion.experience_level}</span>}
                            </div>
                            <p className="si-question-text">{currentQuestion?.question_text}</p>
                        </div>

                        {/* Transcript box */}
                        <div className="si-transcript-box">
                            {finalTranscript || liveTranscript
                                ? <>
                                    <span className="si-transcript-final">{finalTranscript}</span>
                                    <span className="si-transcript-interim">{liveTranscript}</span>
                                  </>
                                : speechSupported
                                    ? <span className="si-transcript-placeholder">
                                        Your transcribed answer will appear here as you speak...
                                      </span>
                                    : <span className="si-transcript-placeholder si-transcript-unsupported">
                                        ⚠️ Live preview unavailable — your browser has blocked the Speech API (common in Brave). Your audio is still recorded and will be transcribed after you submit.
                                      </span>
                            }
                        </div>

                        {/* After recording: show options OR feedback — never both */}
                        {audioURL && !recording && !feedback && (
                            <div className="si-playback">
                                <audio controls src={audioURL} />
                                {submitting ? (
                                    <div className="si-submitting-state">
                                        <span className="si-submitting-spinner" />
                                        <span>⏳ Analysing your answer…</span>
                                    </div>
                                ) : (
                                    <div className="si-choice-row">
                                        <button className="si-choice-btn si-choice-rerecord" onClick={startRecording}>
                                            🔁 Re-record
                                        </button>
                                        <button className="si-choice-btn si-choice-submit" onClick={submitAnswer}>
                                            ✅ Submit Answer
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Feedback — shown only after submit, no re-submit here */}
                        {feedback && (
                            <div className="si-feedback">
                                <h3>📊 Feedback</h3>
                                
                                {/* Main scores - simplified view */}
                                <div className="si-score-grid">
                                    <ScoreBox label="Answer Quality" value={feedback.answer_quality_score} />
                                    <ScoreBox label="Confidence" value={feedback.confidence_score} />
                                </div>

                                {/* Score breakdowns - collapsible */}
                                <details className="si-score-details">
                                    <summary>📈 Answer Quality Breakdown</summary>
                                    <div className="si-score-grid">
                                        <ScoreBox label="Semantic" value={feedback.semantic_score} />
                                        <ScoreBox label="Keywords" value={feedback.keyword_score} />
                                        <ScoreBox label="Completeness" value={feedback.completeness_score} />
                                    </div>
                                </details>

                                <details className="si-score-details">
                                    <summary>📈 Confidence Breakdown</summary>
                                    <div className="si-score-grid">
                                        <ScoreBox label="Grammar" value={feedback.grammar_score} />
                                        <ScoreBox label="Speaking Pace" value={Math.round(feedback.speaking_speed)} suffix=" WPM" />
                                        <ScoreBox label="Filler Words" value={100 - (feedback.filler_count * 10)} />
                                        <ScoreBox label="Long Pauses" value={100 - (feedback.pause_count * 10)} />
                                    </div>
                                </details>

                                {feedback.transcript && (
                                    <div className="si-fb-block">
                                        <h4>📝 Your Transcript</h4>
                                        <p className="si-transcript-text">{feedback.transcript}</p>
                                    </div>
                                )}
                                {feedback.llm_feedback && (
                                    <div className="si-fb-block">
                                        <h4>� Coaching Feedback</h4>
                                        <p>{feedback.llm_feedback}</p>
                                    </div>
                                )}
                                <div className="si-fb-row">
                                    {feedback.strengths && (
                                        <div className="si-fb-block green">
                                            <h4>✅ Strengths</h4>
                                            <ul>
                                                {Array.isArray(feedback.strengths) 
                                                    ? feedback.strengths.map((s, i) => <li key={i}>{s}</li>)
                                                    : <li>{feedback.strengths}</li>
                                                }
                                            </ul>
                                        </div>
                                    )}
                                    {feedback.improvements && (
                                        <div className="si-fb-block orange">
                                            <h4>🔧 Improvements</h4>
                                            <ul>
                                                {Array.isArray(feedback.improvements)
                                                    ? feedback.improvements.map((imp, i) => <li key={i}>{imp}</li>)
                                                    : <li>{feedback.improvements}</li>
                                                }
                                            </ul>
                                        </div>
                                    )}
                                </div>
                                <button className="si-btn-primary si-next-btn" onClick={nextQuestion}>
                                    {currentIndex + 1 >= questions.length
                                        ? "Finish Session 🎉"
                                        : <> Next Question <FiChevronRight /></>}
                                </button>
                            </div>
                        )}
                    </div>

                    {/* RIGHT — voice panel */}
                    <div className="si-right">
                        <div className="si-voice-panel">
                            <h3 className="si-voice-title">Live Voice</h3>
                            <p className="si-voice-subtitle">Speak your answer clearly</p>

                            <div className="si-voice-status-bar">
                                <span className={`si-status-dot ${recording ? "active" : ""}`} />
                                <span className="si-status-text">
                                    {recording ? "Recording..." : audioURL ? "Recorded" : "Ready to record"}
                                </span>
                            </div>

                            <div className="si-waveform">
                                {Array.from({ length: 20 }).map((_, i) => (
                                    <div key={i} className={`si-wave-bar ${recording ? "animated" : ""}`}
                                        style={{ animationDelay: `${i * 0.05}s` }} />
                                ))}
                            </div>

                            {!recording && !audioURL && (
                                <button className="si-mic-btn" onClick={startRecording}>
                                    <FiMic size={28} />
                                </button>
                            )}
                            {recording && (
                                <button className="si-mic-btn recording" onClick={stopRecording}>
                                    <FiSquare size={24} />
                                </button>
                            )}
                            {audioURL && !recording && (
                                <button className="si-mic-btn recorded" onClick={startRecording}>
                                    <FiMic size={28} />
                                </button>
                            )}

                            <p className="si-mic-hint">
                                {recording
                                    ? "Click to stop recording"
                                    : audioURL
                                        ? "Re-record or submit"
                                        : "Tap the microphone to start recording your answer"}
                            </p>

                            <div className="si-status-box">
                                <span className="si-status-label">Status</span>
                                <span className="si-status-value">
                                    {recording ? "🔴 Recording" : audioURL ? "✅ Ready" : "⚪ Ready"}
                                </span>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}

function ScoreBox({ label, value, suffix = "%" }) {
    if (value == null || value === 0 || (suffix === "%" && value === 0)) return null;
    
    // ✅ Backend returns 0-100, don't multiply again!
    const pct = Math.round(value);
    const color = pct >= 70 ? "#4ade80" : pct >= 40 ? "#facc15" : "#f87171";
    
    return (
        <div className="si-score-box">
            <div className="si-score-value" style={{ color }}>{pct}{suffix}</div>
            <div className="si-score-label">{label}</div>
        </div>
    );
}