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
    | "failed"
    | (string & {});

export type DashboardJob = {
    id: number;
    video_id: number;
    provider: string;
    status: DashboardJobStatus;
    scene_index?: number | null;
    error?: string | null;
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
    | "failed"
    | "ready_for_review"
    | "queued"
    | "merging"
    | "publishing"
    | "approved"
    | "rejected"
    | (string & {});

export type DashboardVideo = {
    id: number;
    title?: string | null;
    status: DashboardVideoStatus;
    approval_status?: string | null;
    approved_at?: string | null;
    rejected_at?: string | null;
    scheduled_at?: string | null;
    file_url?: string | null;
    thumbnail_url?: string | null;
    created_at: string;
};
