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
    }
> = {
    totalVideos: {
        title: "Total Videos",
        icon: Video,
    },

    totalViews: {
        title: "Total Views",
        icon: Eye,
    },

    videosThisMonth: {
        title: "Videos This Month",
        icon: Calendar,
    },

    activeJobs: {
        title: "Active Jobs",
        icon: Activity,
    },

    failedJobs: {
        title: "Failed Jobs",
        icon: AlertTriangle, // Admin swap target
    },

    avgProcessingTime: {
        title: "Avg Processing Time",
        icon: Timer,
    },
};
