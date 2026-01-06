/* ===================================================
   DASHBOARD TYPES (BACKEND VERIFIED)
=================================================== */

/* ---------- Metrics ---------- */

export type DashboardMetrics = {
    totalVideos: number;
    videosThisMonth: number;
    activeJobs: number;
    failedJobs: number;
    totalViews?: number | null;
};

/* ---------- Jobs ---------- */

export type DashboardJobStatus =
    | "queued"
    | "running"
    | "success"
    | "failed";

export type DashboardJob = {
    id: number;
    video_id: number;
    provider: string;
    status: DashboardJobStatus;
    scene_index?: number | null;
    created_at: string;
};

export type DashboardJobsResponse = {
    active_jobs: DashboardJob[];
    failed_jobs: DashboardJob[];
};


/* ---------- Videos ---------- */

export type DashboardVideoStatus =
    | "draft"
    | "rendering"
    | "uploaded"
    | "failed";

export type DashboardVideo = {
    id: number;
    title?: string | null;
    status: DashboardVideoStatus;
    file_url?: string | null;
    thumbnail_url?: string | null;
    created_at: string;
};
