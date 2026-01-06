const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL;

function getToken() {
    return localStorage.getItem("access_token");
}

async function apiFetch<T>(
    path: string,
    options?: RequestInit
): Promise<T> {
    const token = getToken();

    const res = await fetch(`${BASE_URL}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            Authorization: token ? `Bearer ${token}` : "",
            ...(options?.headers || {}),
        },
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `API error: ${res.status}`);
    }

    return res.json();
}

/* =========================
   Dashboard APIs
========================= */

export const getDashboardMetrics = () =>
    apiFetch("/dashboard/metrics");

export const getDashboardJobs = () =>
    apiFetch("/dashboard/jobs");

export const getDashboardVideos = () =>
    apiFetch("/dashboard/videos");

/* =========================
   Approval APIs
========================= */

export const approveDashboardVideo = (videoId: number) =>
    apiFetch(`/dashboard/videos/${videoId}/approve`, {
        method: "POST",
    });

export const rejectDashboardVideo = (
    videoId: number,
    reason?: string
) =>
    apiFetch(`/dashboard/videos/${videoId}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason }),
    });
