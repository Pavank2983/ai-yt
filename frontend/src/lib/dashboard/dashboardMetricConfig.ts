import { MetricKey } from "./types";
import { LucideIcon } from "lucide-react";
import {
    Video,
    Eye,
    Calendar,
    Activity,
    AlertTriangle,
    Timer,
} from "lucide-react";

/**
 * Metric display configuration
 * (Titles + icons only — NO role logic here)
 */
export const METRIC_CONFIG: Record<
    MetricKey,
    {
        title: string;
        icon: LucideIcon;
        description?: string;
    }
> = {
    totalVideos: {
        title: "Total Videos",
        icon: Video,
        description: "All generated videos",
    },

    totalViews: {
        title: "Total Views",
        icon: Eye,
        description: "Across published videos",
    },

    videosThisMonth: {
        title: "Videos This Month",
        icon: Calendar,
        description: "Created this month",
    },

    activeJobs: {
        title: "Active Jobs",
        icon: Activity,
        description: "Currently processing",
    },

    failedJobs: {
        title: "Failed Jobs",
        icon: AlertTriangle, // Admin swap target
        description: "Jobs requiring attention",
    },

    avgProcessingTime: {
        title: "Avg Processing Time",
        icon: Timer,
        description: "Average render duration",
    },
};
