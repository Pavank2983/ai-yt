"use client";

import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import StatusBadge from "@/components/common/StatusBadge";

export interface AdminFailedJob {
    id: string | number;
    title: string;
    provider: string;
    error?: string;
}

interface AdminFailedJobsProps {
    jobs: AdminFailedJob[];
    maxItems?: number;
}

export default function AdminFailedJobs({
    jobs,
    maxItems = 5,
}: AdminFailedJobsProps) {
    if (!jobs || jobs.length === 0) return null;

    const visibleJobs = jobs.slice(0, maxItems);

    return (
        <section
            className={cn(
                "rounded-lg border border-red-500/20",
                "bg-red-500/5",
                "p-4 space-y-4"
            )}
        >
            {/* ===================================================
                HEADER
            =================================================== */}
            <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                <AlertTriangle className="h-5 w-5" />
                <h3 className="text-lg font-semibold">
                    Failed Jobs ({jobs.length})
                </h3>
            </div>

            {/* ===================================================
                FAILED JOBS LIST
            =================================================== */}
            <div className="space-y-3">
                {visibleJobs.map((job) => (
                    <div
                        key={job.id}
                        className="
              flex items-center justify-between gap-4
              rounded-md border border-red-500/20
              bg-background/60 px-4 py-3
            "
                    >
                        {/* Job Info */}
                        <div className="min-w-0 space-y-1">
                            <p className="font-medium truncate">
                                {job.title}
                            </p>

                            <p className="text-xs text-muted-foreground">
                                {job.provider}
                                {job.error ? ` • ${job.error}` : ""}
                            </p>
                        </div>

                        {/* Status + Action */}
                        <div className="flex items-center gap-4 shrink-0">
                            <StatusBadge status="failed" size="sm" />

                            <Link
                                href={`/dashboard/jobs/${job.id}`}
                                className="text-sm font-medium text-primary hover:underline"
                            >
                                View
                            </Link>
                        </div>
                    </div>
                ))}
            </div>

            {/* ===================================================
                FOOTER HINT
            =================================================== */}
            {jobs.length > maxItems && (
                <div className="text-xs text-muted-foreground">
                    Showing {maxItems} of {jobs.length} failed jobs
                </div>
            )}
        </section>
    );
}
