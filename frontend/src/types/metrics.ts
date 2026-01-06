export type MetricKey =
    | "totalVideos"
    | "totalViews"
    | "videosThisMonth"
    | "activeJobs"
    | "failedJobs"
    | "avgProcessingTime";

export type Role = "viewer" | "editor" | "admin";

export interface MetricData {
    key: MetricKey;
    label: string;
    value: string | number;
    subText?: string;
}
