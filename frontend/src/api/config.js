// Shared API configuration
// Local dev uses the hardcoded localhost backend; deployed builds use VITE_API_URL.
const DEPLOYED_BACKEND_URL = import.meta.env.VITE_API_URL; // set this to the deployed backend URL

export const BASE_URL = import.meta.env.PROD
    ? DEPLOYED_BACKEND_URL // deployed
    : "http://127.0.0.1:8000"; // local

// Auth helpers — user object stored as JSON in localStorage
export function getAuth() {
    try {
        return JSON.parse(localStorage.getItem("auth") || "null");
    } catch {
        return null;
    }
}

export function setAuth(user) {
    localStorage.setItem("auth", JSON.stringify(user));
}

export function clearAuth() {
    localStorage.removeItem("auth");
}

export function getUserId() {
    return getAuth()?.id ?? null;
}
