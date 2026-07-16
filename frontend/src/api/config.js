// Shared API configuration
export const BASE_URL = "http://127.0.0.1:8000";

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
