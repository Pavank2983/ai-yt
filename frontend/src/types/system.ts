export interface ProviderHealth {
    name: string;
    success_count: number;
    failed_count: number;
    failure_rate: number;
}

export interface SystemMetricsResponse {
    total_spent_today: number;
    projected_spend_today: number;
    budget_limit_per_day: number;
    avg_processing_time_sec: number;
    provider_health: ProviderHealth[];
}
