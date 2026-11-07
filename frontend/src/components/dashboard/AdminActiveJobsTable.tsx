"use client";

import Link from "next/link";
import { Clock, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import StatusBadge, { StatusType } from "@/components/common/StatusBadge";

/* ===================================================
   TYPES
=================================================== */

/**
 * Provider identifiers supported by the system.
 * Extend safely as you add providers.
 */
export type ProviderKey =
    | "MINIMAX"
    | "KLING"
    | "RUNWAY"
    | "SORA"
    | "VEO"
    | "SILICONFLOW"
    | string;

export interface AdminActiveJob {
    id: string | number;
    title?: string;
    video_id?: number;
    provider: ProviderKey;
    status: string;
    startedAt?: string; // e.g. "5 mins ago"
    runtime?: string;   // e.g. "1m 12s"
}

/* ===================================================
   PROVIDER BADGE (ICON + TEXT)
=================================================== */

function ProviderBadge({ provider }: { provider: ProviderKey }) {
    return (
        <span
            className={cn(
                "inline-flex items-center gap-2",
                "rounded-md border px-2 py-1 text-xs font-medium",
                "bg-muted/40"
            )}
        >
            <Activity className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="truncate max-w-[100px]">
                {provider.toUpperCase()}
            </span>
        </span>
    );
}

/* ===================================================
   COMPONENT
=================================================== */

interface AdminActiveJobsTableProps {
    jobs: AdminActiveJob[];
    maxItems?: number;
}

export default function AdminActiveJobsTable({
    jobs,
    maxItems = 5,
}: AdminActiveJobsTableProps) {
    if (!jobs || jobs.length === 0) {
        return (
            <div className="text-sm text-muted-foreground">
                No active jobs. All caught up 🎉
            </div>
        );
    }

    const visibleJobs = jobs.slice(0, maxItems);

    /**
     * Map internal job status → UI status badge
     * Keeps backend + UI decoupled
     */
    const mapStatus = (status: AdminActiveJob["status"]): StatusType => {
        switch (status) {
            case "queued":
                return "queued";
            case "running":
                return "running";
            default:
                return "queued";
        }
    };

    return (
        <section className="space-y-4">
            <h3 className="text-lg font-semibold">Active Jobs</h3>

            <div className="rounded-lg border overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-muted/40">
                        <tr className="text-left">
                            <th className="px-4 py-2 font-medium">Job</th>
                            <th className="px-4 py-2 font-medium">Provider</th>
                            <th className="px-4 py-2 font-medium">Status</th>
                            <th className="px-4 py-2 font-medium">Runtime</th>
                            <th className="px-4 py-2 font-medium text-right">Action</th>
                        </tr>
                    </thead>

                    <tbody>
                        {visibleJobs.map((job) => (
                            <tr
                                key={job.id}
                                className="border-t hover:bg-muted/30 transition-colors"
                            >
                                {/* Job */}
                                <td className="px-4 py-3">
                                    <p className="font-medium truncate max-w-[280px]">
                                        {job.title ?? `Video #${job.video_id ?? job.id}`}
                                    </p>
                                    {job.startedAt && (
                                        <p className="text-xs text-muted-foreground mt-0.5">
                                            Started {job.startedAt}
                                        </p>
                                    )}
                                </td>

                                {/* Provider */}
                                <td className="px-4 py-3">
                                    <ProviderBadge provider={job.provider} />
                                </td>

                                {/* Status (COMMON COMPONENT) */}
                                <td className="px-4 py-3">
                                    <StatusBadge
                                        status={mapStatus(job.status)}
                                        size="sm"
                                    />
                                </td>

                                {/* Runtime */}
                                <td className="px-4 py-3">
                                    <div className="flex items-center gap-1 text-muted-foreground">
                                        <Clock className="h-3.5 w-3.5" />
                                        <span className="text-xs">
                                            {job.runtime ?? "-"}
                                        </span>
                                    </div>
                                </td>

                                {/* Action */}
                                <td className="px-4 py-3 text-right">
                                    <Link
                                        href={`/dashboard/jobs/${job.id}`}
                                        className="text-sm font-medium text-primary hover:underline"
                                    >
                                        View
                                    </Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {jobs.length > maxItems && (
                <div className="text-xs text-muted-foreground">
                    Showing {maxItems} of {jobs.length} active jobs
                </div>
            )}
        </section>
    );
}
