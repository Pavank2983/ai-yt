"use client";

import { cn } from "@/lib/utils";
import {
    CheckCircle,
    Clock,
    AlertCircle,
    Loader,
    FileText,
    XCircle,
    ShieldCheck,
} from "lucide-react";
import { LucideIcon } from "lucide-react";

/* ===================================================
   STATUS TYPES (BACKEND-ALIGNED)
=================================================== */

export type StatusType =
    /* -------- VIDEO PIPELINE -------- */
    | "draft"
    | "rendering"
    | "ready_for_review"
    | "uploaded"
    | "failed"

    /* -------- APPROVAL -------- */
    | "pending_review"
    | "approved"
    | "rejected"

    /* -------- JOB -------- */
    | "queued"
    | "running"
    | "success";

const STATUS_VALUES: StatusType[] = [
    "draft", "rendering", "ready_for_review", "uploaded", "failed",
    "pending_review", "approved", "rejected", "queued", "running", "success",
];

export function normalizeStatus(value: string): StatusType {
    return STATUS_VALUES.includes(value as StatusType)
        ? (value as StatusType)
        : "draft";
}

/* ===================================================
   STATUS CONFIG (SINGLE SOURCE OF TRUTH)
=================================================== */

const STATUS_CONFIG: Record<
    StatusType,
    {
        label: string;
        icon: LucideIcon;
        className: string;
    }
> = {
    /* -------- VIDEO -------- */

    draft: {
        label: "Draft",
        icon: FileText,
        className:
            "bg-muted/40 text-muted-foreground border border-border",
    },

    rendering: {
        label: "Rendering",
        icon: Clock,
        className:
            "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30",
    },

    ready_for_review: {
        label: "Waiting for Review",
        icon: Clock,
        className:
            "bg-blue-500/15 text-blue-400 border border-blue-500/30",
    },

    uploaded: {
        label: "Published",
        icon: CheckCircle,
        className:
            "bg-green-500/15 text-green-400 border border-green-500/30",
    },

    failed: {
        label: "Failed",
        icon: AlertCircle,
        className:
            "bg-red-500/15 text-red-400 border border-red-500/30",
    },

    /* -------- APPROVAL -------- */

    pending_review: {
        label: "Pending Approval",
        icon: Clock,
        className:
            "bg-blue-500/15 text-blue-400 border border-blue-500/30",
    },

    approved: {
        label: "Approved",
        icon: ShieldCheck,
        className:
            "bg-green-500/15 text-green-400 border border-green-500/30",
    },

    rejected: {
        label: "Rejected",
        icon: XCircle,
        className:
            "bg-red-500/15 text-red-400 border border-red-500/30",
    },

    /* -------- JOB -------- */

    queued: {
        label: "Queued",
        icon: Loader,
        className:
            "bg-blue-500/15 text-blue-400 border border-blue-500/30",
    },

    running: {
        label: "Running",
        icon: Clock,
        className:
            "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30",
    },

    success: {
        label: "Completed",
        icon: CheckCircle,
        className:
            "bg-green-500/15 text-green-400 border border-green-500/30",
    },
};

/* ===================================================
   COMPONENT PROPS
=================================================== */

interface StatusBadgeProps {
    status: StatusType;
    size?: "sm" | "md";
    showIcon?: boolean;
    className?: string;
}

/* ===================================================
   COMPONENT
=================================================== */

export default function StatusBadge({
    status,
    size = "md",
    showIcon = true,
    className,
}: StatusBadgeProps) {
    const config = STATUS_CONFIG[status];
    if (!config) return null;

    const Icon = config.icon;

    return (
        <span
            className={cn(
                "inline-flex items-center gap-1.5 rounded-full font-medium",
                "backdrop-blur-sm select-none",
                size === "sm" && "px-2 py-0.5 text-xs",
                size === "md" && "px-3 py-1 text-sm",
                config.className,
                className
            )}
        >
            {showIcon && <Icon className="h-3.5 w-3.5" />}
            <span>{config.label}</span>
        </span>
    );
}
