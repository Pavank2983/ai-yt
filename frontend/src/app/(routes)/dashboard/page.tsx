"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useQuery } from "@tanstack/react-query";

import MetricsCard from "@/components/dashboard/MetricsCard";
import VideoCard from "@/components/dashboard/VideoCard";
import AdminFailedJobs from "@/components/dashboard/AdminFailedJobs";
import AdminActiveJobsTable from "@/components/dashboard/AdminActiveJobsTable";

import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

import { METRIC_CONFIG } from "@/lib/dashboard/dashboardMetricConfig";
import {
  ROLE_METRICS,
  resolveAdminMetrics,
} from "@/lib/dashboard/dashboardMetrics";
import { MetricKey } from "@/lib/dashboard/types";

import {
  getDashboardMetrics,
  getDashboardJobs,
  getDashboardVideos,
} from "@/lib/api/dashboard";

/* =========================
   CENTRALIZED TYPES
========================= */

import type {
  DashboardMetrics,
  DashboardVideo,
  DashboardJobsResponse,
} from "@/types/dashboard";

export default function DashboardOverviewPage() {
  const { user } = useAuth();
  const role = user?.role ?? "viewer";
  const isViewer = role === "viewer";
  const isEditor = role === "editor";
  const isAdmin = role === "admin";

  /* =========================
     QUERIES
  ========================= */

  const { data: metrics } = useQuery<DashboardMetrics>({
    queryKey: ["dashboard-metrics"],
    queryFn: getDashboardMetrics,
    enabled: !!user,
  });

  const { data: jobs } = useQuery<DashboardJobsResponse>({
    queryKey: ["dashboard-jobs"],
    queryFn: getDashboardJobs,
    enabled: isAdmin || isEditor,
  });

  const { data: videos } = useQuery<DashboardVideo[]>({
    queryKey: ["dashboard-videos"],
    queryFn: getDashboardVideos,
    enabled: !!user,
  });

  if (!user) return null;

  /* =========================
     METRICS
  ========================= */

  let metricKeys: MetricKey[] = ROLE_METRICS[role];

  if (isAdmin) {
    metricKeys = resolveAdminMetrics(
      ROLE_METRICS.admin,
      jobs?.failed_jobs?.length ?? 0
    );
  }

  /* =========================
     JOBS
  ========================= */

  const failedJobs = jobs?.failed_jobs ?? [];
  const activeJobs = jobs?.active_jobs ?? [];

  /* =========================
     VIDEOS
  ========================= */

  const visibleVideos =
    videos?.filter((video) =>
      isViewer ? video.status === "uploaded" : true
    ) ?? [];

  return (
    <div className="space-y-12">
      {/* ================= HEADER ================= */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground mt-1">
            Welcome back, {user.name?.split(" ")[0] || "User"}.
          </p>
        </div>
      </div>

      {/* ================= METRICS ================= */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metricKeys.map((key) => {
          const config = METRIC_CONFIG[key];
          const value = key === "avgProcessingTime" ? 0 : metrics?.[key] ?? 0;

          return (
            <MetricsCard
              key={key}
              title={config.title}
              value={value}
              description={config.description}
              icon={config.icon}
            />
          );
        })}
      </div>

      {/* ================= ADMIN: FAILED JOBS ================= */}
      {isAdmin && <AdminFailedJobs jobs={failedJobs} />}

      {/* ================= ADMIN + EDITOR: ACTIVE JOBS ================= */}
      {(isAdmin || isEditor) && (
        <AdminActiveJobsTable jobs={activeJobs} />
      )}

      {/* ================= RECENT VIDEOS ================= */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold">Recent Videos</h3>

          <Button variant="ghost" size="sm" asChild>
            <Link
              href="/dashboard/videos"
              className="flex items-center text-primary"
            >
              View All <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </Button>
        </div>

        {visibleVideos.length === 0 ? (
          <div className="text-muted-foreground text-sm py-12 text-center">
            {isViewer
              ? "No videos published yet."
              : "You haven’t created any videos yet."}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {visibleVideos.map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
