import { MetricKey } from "./types";

/**
 * Role → default metric order
 * (Max 5 metrics, locked)
 */
export const ROLE_METRICS: Record<
    "viewer" | "editor" | "admin",
    MetricKey[]
> = {
    viewer: ["totalVideos"],

    editor: [
        "totalVideos",
        "videosThisMonth",
        "activeJobs",
        "avgProcessingTime",
    ],

    admin: [
        "totalVideos",
        "totalViews",
        "videosThisMonth",
        "activeJobs",          // may be swapped with failedJobs
        "avgProcessingTime",
    ],
};

/**
 * Utility to resolve Admin metrics dynamically
 * If failedJobsCount > 0:
 *  - Replace "activeJobs" with "failedJobs"
 */
export function resolveAdminMetrics(
    baseMetrics: MetricKey[],
    failedJobsCount: number
): MetricKey[] {
    if (failedJobsCount <= 0) return baseMetrics;

    return baseMetrics.map((key) =>
        key === "activeJobs" ? "failedJobs" : key
    );
}
