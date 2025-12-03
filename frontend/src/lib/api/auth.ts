/* ============================================================
   BASE CONFIG
============================================================ */
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_API_URL;

/* Safely parse JSON */
async function safeJson(res: Response) {
    try {
        return await res.json();
    } catch {
        return null;
    }
}

/* Unified response handler */
async function handleApiResponse(res: Response) {
    const data = await safeJson(res);

    if (res.ok) return data;

    // Extract backend errors correctly
    if (data?.detail) {
        throw new Error(
            typeof data.detail === "string"
                ? data.detail
                : Array.isArray(data.detail)
                ? data.detail[0]?.msg || "Request failed"
                : "Request failed"
        );
    }

    throw new Error("Something went wrong. Please try again.");
}

/* Generic fetch wrapper */
async function apiFetch(url: string, options: RequestInit = {}) {
    const res = await fetch(url, {
        ...options,
        credentials: "include", // allow cookies to pass
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    return handleApiResponse(res);
}

/* ============================================================
   LOGIN
============================================================ */
export async function loginUser(email: string, password: string) {
    try {
        return await apiFetch(`${API_BASE}/auth/login`, {
            method: "POST",
            body: JSON.stringify({ email, password })
        });
    } catch (err: any) {
        console.error("❌ Login Error:", err);
        throw new Error(err.message || "Login failed");
    }
}

/* ============================================================
   REGISTER
============================================================ */
export async function registerUser(
    name: string,
    email: string,
    password: string
) {
    try {
        return await apiFetch(`${API_BASE}/auth/register`, {
            method: "POST",
            body: JSON.stringify({ name, email, password })
        });
    } catch (err: any) {
        console.error("❌ Register Error:", err);
        throw new Error(err.message || "Registration failed");
    }
}

/* ============================================================
   GET CURRENT USER
   (Checks if token is valid using /auth/me)
============================================================ */
export async function getCurrentUser() {
    try {
        return await apiFetch(`${API_BASE}/auth/me`, {
            method: "GET"
        });
    } catch {
        return null; // not logged in
    }
}

/* ============================================================
   LOGOUT
============================================================ */
export async function logoutUser() {
    try {
        await fetch(`${API_BASE}/auth/logout`, {
            method: "POST",
            credentials: "include",
        });
    } catch (e) {
        console.error("Logout error:", e);
    }

    // redirect after logout
    window.location.href = "/";
}


/* ============================================================
   Get USER TOKEN from cookies
============================================================ */
export function getUserToken() {
    
    if (typeof window === "undefined") return null;
    return document.cookie
        .split("; ")
        .find((row) => row.startsWith("access_token="))
        ?.split("=")[1] || null;
}