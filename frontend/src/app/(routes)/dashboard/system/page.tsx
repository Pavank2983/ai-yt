"use client";

import { useAuth } from "@/context/AuthContext";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import {
    Activity,
    Server,
    Cpu,
    DollarSign,
    AlertTriangle,
    CheckCircle2,
} from "lucide-react";

import { getSystemMetrics } from "@/lib/api/system";
import type { SystemMetricsResponse } from "@/types/system";

export default function SystemObservabilityPage() {
    const { user } = useAuth();
    const router = useRouter();

    const isAdmin = user?.role === "admin";

    const { data, isLoading, isError } = useQuery<SystemMetricsResponse>({
        queryKey: ["system-metrics"],
        queryFn: getSystemMetrics,
        enabled: isAdmin,
    });

    if (!user) return null;

    // 🔒 Admin-only protection
    if (!isAdmin) {
        router.push("/dashboard");
        return null;
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-32">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
        );
    }

    if (isError || !data) {
        return (
            <div className="text-center py-20 text-muted-foreground">
                Failed to load system metrics.
            </div>
        );
    }

    // 🔐 SAFE NUMERIC EXTRACTION
    const total_spent_today = Number(data.cost.today_spend ?? 0);
    const projected_spend_today = data.cost.spend_by_provider_24h["projected"] ?? null;
    const budget_limit_per_day = Number(process.env.NEXT_PUBLIC_DAILY_BUDGET ?? 0) || null;
    const avg_processing_time_sec = Number(data.jobs.avg_render_time_seconds ?? 0);

    const provider_health = Object.entries(data.provider_health_24h).map(
        ([name, provider]) => ({
            name,
            success_count: provider.success_count,
            failed_count: provider.failure_count,
            failure_rate: 1 - provider.success_rate_percent / 100,
        })
    );

    const budgetExceeded =
        budget_limit_per_day !== null &&
        projected_spend_today !== null &&
        projected_spend_today > budget_limit_per_day;

    return (
        <div className="space-y-10">
            {/* ================= HEADER ================= */}
            <div>
                <h2 className="text-3xl font-bold tracking-tight">
                    System Observability
                </h2>
                <p className="text-muted-foreground mt-1">
                    Infrastructure health, cost tracking, and performance monitoring.
                </p>
            </div>

            {/* ================= SYSTEM METRICS ================= */}
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <Card className="rounded-2xl">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="text-sm font-medium">
                            Today’s Spend
                        </CardTitle>
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent className="text-2xl font-bold">
                        ${total_spent_today.toFixed(2)}
                    </CardContent>
                </Card>

                <Card className="rounded-2xl">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="text-sm font-medium">
                            Projected Spend
                        </CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent className="text-2xl font-bold">
                        {projected_spend_today === null
                            ? "N/A"
                            : `$${projected_spend_today.toFixed(2)}`}
                    </CardContent>
                </Card>

                <Card className="rounded-2xl">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="text-sm font-medium">
                            Daily Budget Limit
                        </CardTitle>
                        <Server className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent className="text-2xl font-bold">
                        {budget_limit_per_day === null
                            ? "Not configured"
                            : `$${budget_limit_per_day.toFixed(2)}`}
                    </CardContent>
                </Card>

                <Card className="rounded-2xl">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="text-sm font-medium">
                            Avg Processing Time
                        </CardTitle>
                        <Cpu className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent className="text-2xl font-bold">
                        {avg_processing_time_sec.toFixed(1)}s
                    </CardContent>
                </Card>
            </div>

            {/* ================= BUDGET STATUS ================= */}
            <Card className="rounded-2xl">
                <CardHeader>
                    <CardTitle>Budget Guardrail Status</CardTitle>
                </CardHeader>
                <CardContent className="flex items-center gap-3">
                    {budgetExceeded ? (
                        <>
                            <AlertTriangle className="h-5 w-5 text-red-500" />
                            <Badge variant="destructive">
                                Budget Limit Exceeded
                            </Badge>
                        </>
                    ) : (
                        <>
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                            <Badge variant="secondary">
                                Within Budget
                            </Badge>
                        </>
                    )}
                </CardContent>
            </Card>

            {/* ================= PROVIDER HEALTH ================= */}
            <div>
                <h3 className="text-xl font-semibold mb-4">
                    Provider Health
                </h3>

                <Card className="rounded-2xl">
                    <CardContent className="p-6 space-y-6">
                        {provider_health.length === 0 ? (
                            <div className="text-sm text-muted-foreground">
                                No provider data available (last 24h).
                            </div>
                        ) : (
                            provider_health.map((provider) => {
                                const failureRate =
                                    Number(provider?.failure_rate ?? 0) * 100;

                                return (
                                    <div key={provider.name}>
                                        <div className="flex items-center justify-between">
                                            <div className="font-medium">
                                                {provider.name}
                                            </div>

                                            <Badge
                                                variant={
                                                    failureRate > 30
                                                        ? "destructive"
                                                        : "secondary"
                                                }
                                            >
                                                {failureRate.toFixed(1)}% failure
                                            </Badge>
                                        </div>

                                        <Separator className="my-3" />

                                        <div className="text-sm text-muted-foreground">
                                            Success: {Number(provider?.success_count ?? 0)} | Failed:{" "}
                                            {Number(provider?.failed_count ?? 0)}
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
