/* ============================================================
   BASE CONFIG
============================================================ */
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_API_URL;

/* ============================================================
   SAFE JSON PARSER
============================================================ */
async function safeJson(res: Response) {
    try {
        return await res.json();
    } catch {
        return null;
    }
}

/* ============================================================
   UNIFIED RESPONSE HANDLER
============================================================ */
async function handleApiResponse(res: Response) {
    const data = await safeJson(res);

    if (res.ok) return data;

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

/* ============================================================
   GENERIC FETCH WRAPPER (COOKIE-BASED AUTH)
============================================================ */
async function apiFetch(url: string, options: RequestInit = {}) {
    const res = await fetch(url, {
        ...options,
        credentials: "include", // ✅ cookies auto-attached
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        },
    });

    return handleApiResponse(res);
}

/* ============================================================
   LOGIN
============================================================ */
export async function loginUser(email: string, password: string) {
    return apiFetch(`${API_BASE}/auth/login`, {
        method: "POST",
        body: JSON.stringify({ email, password }),
    });
}

/* ============================================================
   REGISTER
============================================================ */
export async function registerUser(
    name: string,
    email: string,
    password: string
) {
    return apiFetch(`${API_BASE}/auth/register`, {
        method: "POST",
        body: JSON.stringify({ name, email, password }),
    });
}

/* ============================================================
   GET CURRENT USER
============================================================ */
export async function getCurrentUser() {
    try {
        return await apiFetch(`${API_BASE}/auth/me`, {
            method: "GET",
        });
    } catch {
        return null;
    }
}

/* ============================================================
   LOGOUT
============================================================ */
export async function logoutUser() {
    try {
        await apiFetch(`${API_BASE}/auth/logout`, {
            method: "POST",
        });
    } catch (err) {
        console.error("Logout error:", err);
    } finally {
        window.location.href = "/";
    }
}
