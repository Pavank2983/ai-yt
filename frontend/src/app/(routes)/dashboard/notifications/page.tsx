"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Bell, CheckCircle2, AlertTriangle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

// Types
interface NotificationItem {
    id: number;
    title: string;
    message: string;
    time: string;
    type: "success" | "warning" | "info" | "error";
    read: boolean;
}

// Mock Notifications
const NOTIFICATIONS: NotificationItem[] = [
    {
        id: 1,
        title: "Video Generation Complete",
        message:
            "Your video 'Top 10 AI Tools' has finished rendering and is ready for review.",
        time: "2 min ago",
        type: "success",
        read: false,
    },
    {
        id: 2,
        title: "Credits Low",
        message: "You have used 80% of your monthly generation credits.",
        time: "1 hour ago",
        type: "warning",
        read: false,
    },
    {
        id: 3,
        title: "System Update",
        message:
            "We have added 5 new voices to the library. Check them out!",
        time: "1 day ago",
        type: "info",
        read: true,
    },
    {
        id: 4,
        title: "Job Failed",
        message:
            "Video generation for 'Mars Rover' failed due to asset timeout.",
        time: "2 days ago",
        type: "error",
        read: true,
    },
];

// PAGE COMPONENT
export default function NotificationsPage() {
    return (
        <div className="max-w-2xl mx-auto space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Notifications</h2>
                    <p className="text-muted-foreground">
                        Stay updated with system alerts and video generation status.
                    </p>
                </div>

                <Button variant="outline" size="sm">
                    Mark all as read
                </Button>
            </div>

            {/* Notification List */}
            <div className="space-y-4">
                {NOTIFICATIONS.map((notification) => (
                    <Card
                        key={notification.id}
                        className={cn(
                            "transition-colors",
                            !notification.read && "border-primary/40 bg-primary/5"
                        )}
                    >
                        <CardContent className="p-4 flex gap-4 items-start">
                            {/* Icon */}
                            <div
                                className={cn(
                                    "mt-1 h-8 w-8 rounded-full flex items-center justify-center shrink-0",
                                    notification.type === "success"
                                        ? "bg-green-500/10 text-green-500"
                                        : notification.type === "warning"
                                            ? "bg-yellow-500/10 text-yellow-500"
                                            : notification.type === "error"
                                                ? "bg-red-500/10 text-red-500"
                                                : "bg-blue-500/10 text-blue-500"
                                )}
                            >
                                {notification.type === "success" && (
                                    <CheckCircle2 className="h-4 w-4" />
                                )}
                                {notification.type === "warning" && (
                                    <AlertTriangle className="h-4 w-4" />
                                )}
                                {notification.type === "error" && (
                                    <X className="h-4 w-4" />
                                )}
                                {notification.type === "info" && (
                                    <Info className="h-4 w-4" />
                                )}
                            </div>

                            {/* Content */}
                            <div className="flex-1 space-y-1">
                                <div className="flex justify-between items-start">
                                    <p
                                        className={cn(
                                            "font-medium text-sm",
                                            !notification.read && "text-foreground"
                                        )}
                                    >
                                        {notification.title}
                                    </p>
                                    <span className="text-xs text-muted-foreground">
                                        {notification.time}
                                    </span>
                                </div>

                                <p className="text-sm text-muted-foreground leading-relaxed">
                                    {notification.message}
                                </p>
                            </div>

                            {/* Unread dot */}
                            {!notification.read && (
                                <div className="h-2 w-2 bg-primary rounded-full mt-2" />
                            )}
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
}
