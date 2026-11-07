import type {
    DashboardJobsResponse,
    DashboardMetrics,
    DashboardVideo,
} from "@/types/dashboard";

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

    return res.json() as Promise<T>;
}

/* =========================
   Dashboard APIs
========================= */

export const getDashboardMetrics = (): Promise<DashboardMetrics> =>
    apiFetch<DashboardMetrics>("/dashboard/metrics");

export const getDashboardJobs = (): Promise<DashboardJobsResponse> =>
    apiFetch<DashboardJobsResponse>("/dashboard/jobs");

export const getDashboardVideos = (): Promise<DashboardVideo[]> =>
    apiFetch<DashboardVideo[]>("/dashboard/videos");

/* =========================
   Approval APIs
========================= */

export const approveDashboardVideo = (videoId: number): Promise<DashboardVideo> =>
    apiFetch<DashboardVideo>(`/dashboard/videos/${videoId}/approve`, {
        method: "POST",
    });

export const rejectDashboardVideo = (
    videoId: number,
    reason?: string
): Promise<DashboardVideo> =>
    apiFetch<DashboardVideo>(`/dashboard/videos/${videoId}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason }),
    });
