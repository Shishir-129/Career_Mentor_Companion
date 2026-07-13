import { useState, useRef, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { createSession, getQuestionsForSession, submitAudioResponse } from "../api/interviewApi";
import { FiMic, FiSquare, FiChevronRight } from "react-icons/fi";
import "./StartInterview.css";

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
    const recognitionRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);

    const [timer, setTimer] = useState(0);
    const timerRef = useRef(null);

    const userId = 1;

    useEffect(() => {
        if (!role) { navigate("/new-interview"); return; }
        const init = async () => {
            try {
                const sessionData = await createSession(userId, role);
                setSessionId(sessionData.id);
                const questionsData = await getQuestionsForSession(
                    role,
                    experience,        // ✅ "fresher" / "junior" / "mid-level" / "senior"
                    interviewType,     // ✅ passed as-is, backend handles case-insensitive
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

    const formatTime = (s) =>
        `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

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
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
            mediaRecorder.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: "audio/webm" });
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
        if (!SpeechRecognition) return;
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
        recognition.start();
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
            const result = await submitAudioResponse({
                sessionId, userId,
                questionId: currentQuestion.id,
                questionType: currentQuestion.question_type,
                topic: currentQuestion.topic,
                audioBlob,
            });
            setFeedback(result);
        } catch (err) {
            console.error(err);
            alert("Failed to submit answer.");
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
        <div className="app-layout"><Sidebar />
            <div className="si-wrapper si-center">
                <div className="complete-card">
                    <h1>🎉 Session Complete!</h1>
                    <p>You answered all {questions.length} questions for <strong>{role}</strong>.</p>
                    <button className="si-btn-primary" onClick={() => navigate("/new-interview")}>
                        Start New Interview
                    </button>
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
                                : <span className="si-transcript-placeholder">
                                    Your transcribed answer will appear here as you speak...
                                  </span>
                            }
                        </div>

                        {/* Playback */}
                        {audioURL && !recording && (
                            <div className="si-playback">
                                <audio controls src={audioURL} />
                                <div className="si-playback-actions">
                                    <button className="si-btn-secondary" onClick={startRecording}>🔁 Re-record</button>
                                    <button className="si-btn-primary" onClick={submitAnswer} disabled={submitting}>
                                        {submitting ? "⏳ Analysing..." : "✅ Submit Answer"}
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Feedback */}
                        {feedback && (
                            <div className="si-feedback">
                                <h3>📊 Feedback</h3>
                                <div className="si-score-grid">
                                    <ScoreBox label="Answer Quality" value={feedback.answer_quality_score} />
                                    <ScoreBox label="Semantic" value={feedback.semantic_score} />
                                    <ScoreBox label="Keywords" value={feedback.keyword_score} />
                                    <ScoreBox label="Confidence" value={feedback.confidence_score} />
                                    <ScoreBox label="Grammar" value={feedback.grammar_score} />
                                    <ScoreBox label="Completeness" value={feedback.completeness_score} />
                                </div>

                                {feedback.transcript && (
                                    <div className="si-fb-block">
                                        <h4>📝 Your Transcript</h4>
                                        <p className="si-transcript-text">{feedback.transcript}</p>
                                    </div>
                                )}
                                {feedback.llm_feedback && (
                                    <div className="si-fb-block">
                                        <h4>💬 AI Feedback</h4>
                                        <p>{feedback.llm_feedback}</p>
                                    </div>
                                )}
                                <div className="si-fb-row">
                                    {feedback.strengths && (
                                        <div className="si-fb-block green">
                                            <h4>✅ Strengths</h4>
                                            <p>{feedback.strengths}</p>
                                        </div>
                                    )}
                                    {feedback.improvements && (
                                        <div className="si-fb-block orange">
                                            <h4>🔧 Improvements</h4>
                                            <p>{feedback.improvements}</p>
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

function ScoreBox({ label, value }) {
    if (value == null) return null;
    const pct = Math.round(value * 100);
    const color = pct >= 70 ? "#4ade80" : pct >= 40 ? "#facc15" : "#f87171";
    return (
        <div className="si-score-box">
            <div className="si-score-value" style={{ color }}>{pct}%</div>
            <div className="si-score-label">{label}</div>
        </div>
    );
}