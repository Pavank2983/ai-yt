export type MetricKey =
    | "totalVideos"
    | "totalViews"
    | "videosThisMonth"
    | "activeJobs"
    | "failedJobs"
    | "avgProcessingTime";

export interface MetricValueBase {
    description?: string;
    trend?: string;
    trendUp?: boolean;
}

export interface NumericMetricValue extends MetricValueBase {
    value: number;
}

export interface DisplayMetricValue extends MetricValueBase {
    value: string | number;
}
