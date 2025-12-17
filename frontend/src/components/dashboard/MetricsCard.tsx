"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface MetricsCardProps {
    title: string;
    value: string | number;
    description?: string;
    trend?: string | number;
    trendUp?: boolean;
    icon?: LucideIcon;
}

export default function MetricsCard({
    title,
    value,
    description,
    trend,
    trendUp,
    icon: Icon,
}: MetricsCardProps) {
    return (
        <Card className="overflow-hidden border-border/50 shadow-sm hover:shadow-md transition-all duration-300">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                    {title}
                </CardTitle>

                {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
            </CardHeader>

            <CardContent>
                <div className="text-2xl font-bold tracking-tight">{value}</div>

                <div className="flex items-center pt-1">
                    {trend !== undefined && (
                        <span
                            className={cn(
                                "text-xs font-medium mr-2",
                                trendUp ? "text-green-500" : "text-red-500"
                            )}
                        >
                            {trendUp ? "+" : ""}
                            {trend}
                        </span>
                    )}

                    {description && (
                        <p className="text-xs text-muted-foreground">{description}</p>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
