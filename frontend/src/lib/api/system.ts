import type { SystemMetricsResponse } from "@/types/system";

export async function getSystemMetrics() {
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/dashboard/system-metrics`,
        {
            credentials: "include",
        }
    );

    if (!res.ok) {
        const error = new Error("Failed to fetch system metrics");
        Object.assign(error, { status: res.status });
        throw error;
    }

    return res.json() as Promise<SystemMetricsResponse>;
}
