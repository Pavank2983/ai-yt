"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/context/AuthContext";

import AdminActiveJobsTable from "@/components/dashboard/AdminActiveJobsTable";
import AdminFailedJobs from "@/components/dashboard/AdminFailedJobs";

import { getDashboardJobs } from "@/lib/api/dashboard";
import type {
    DashboardJobsResponse,
} from "@/types/dashboard";

export default function DashboardJobsPage() {
    const { user } = useAuth();

    // Safety guard — viewer should never access jobs
    const isAdmin = user?.role === "admin";
    const isEditor = user?.role === "editor";

    const { data: jobs } = useQuery<DashboardJobsResponse>({
        queryKey: ["dashboard-jobs"],
        queryFn: getDashboardJobs,
        enabled: isAdmin || isEditor,
    });

    if (!user || user.role === "viewer") {
        return null;
    }

    /* =========================
       JOB DATA (SAFE)
    ========================= */

    const activeJobs = jobs?.active_jobs ?? [];
    const failedJobs = jobs?.failed_jobs ?? [];

    return (
        <div className="space-y-8">
            {/* =========================
               Active Jobs
               (Admin + Editor)
            ========================= */}
            <AdminActiveJobsTable jobs={activeJobs} />

            {/* =========================
               Failed Jobs
               (Admin only)
            ========================= */}
            {isAdmin && (
                <AdminFailedJobs jobs={failedJobs} />
            )}
        </div>
    );
}
