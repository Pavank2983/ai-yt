export interface SystemMetricsResponse {
    cost: {
        today_spend: number;
        total_spend_all_time: number;
        spend_by_provider_24h: Record<string, number>;
    };
    videos: {
        rendering: number;
        ready_for_review: number;
        failed_today: number;
    };
    jobs: {
        queued: number;
        running: number;
        failed_today: number;
        retry_rate_percent: number;
        avg_render_time_seconds: number;
    };
    provider_health_24h: Record<string, {
        total_jobs: number;
        success_count: number;
        failure_count: number;
        success_rate_percent: number;
    }>;
}
