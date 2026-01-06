"use client";

import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Play, MoreVertical, Clock, Eye, Calendar } from "lucide-react";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import StatusBadge, { StatusType } from "@/components/common/StatusBadge";

/* ===================================================
   TYPES
=================================================== */

export interface VideoCardProps {
    video: {
        id: string | number;
        title: string;
        thumbnail?: string | null;
        status: StatusType;              // pipeline status
        approval_status?: StatusType;    // approval status
        views?: string | number;
        duration?: string | null;
        date?: string | null;
        external_url?: string; // Viewer redirect
    };
}

/* ===================================================
   COMPONENT
=================================================== */

export default function VideoCard({ video }: VideoCardProps) {
    const router = useRouter();
    const { user } = useAuth();

    const isViewer = user?.role === "viewer";

    const handleNavigate = () => {
        if (isViewer && video.external_url) {
            window.open(video.external_url, "_blank");
            return;
        }
        router.push(`/dashboard/videos/${video.id}`);
    };

    return (
        <Card
            onClick={isViewer ? handleNavigate : undefined}
            className={cn(
                "group overflow-hidden border-border/50 transition-all duration-300 flex flex-col h-full",
                isViewer
                    ? "cursor-pointer hover:border-primary/40"
                    : "hover:border-primary/50"
            )}
        >
            {/* ===================================================
                THUMBNAIL
            =================================================== */}
            <div className="relative aspect-[9/16] bg-muted overflow-hidden">
                {video.thumbnail ? (
                    <Image
                        src={video.thumbnail}
                        alt={video.title}
                        fill
                        unoptimized
                        className="object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center bg-muted/50">
                        <Play className="h-12 w-12 text-muted-foreground/30" />
                    </div>
                )}

                {/* Hover overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

                {/* Status Badges (Editor/Admin only) */}
                {!isViewer && (
                    <>
                        {/* Pipeline Status */}
                        <div className="absolute top-2 right-2">
                            <StatusBadge status={video.status} size="sm" />
                        </div>

                        {/* Approval Status */}
                        {video.approval_status && (
                            <div className="absolute top-2 left-2">
                                <StatusBadge
                                    status={video.approval_status}
                                    size="sm"
                                />
                            </div>
                        )}
                    </>
                )}

                {/* Play Button */}
                <div className="absolute bottom-3 right-3 opacity-0 translate-y-2 transition-all duration-300 group-hover:opacity-100 group-hover:translate-y-0">
                    <Button
                        size="icon"
                        className="rounded-full h-10 w-10 bg-white text-black hover:bg-white/90 shadow-lg"
                        onClick={(e) => {
                            e.stopPropagation();
                            handleNavigate();
                        }}
                    >
                        <Play className="h-4 w-4 ml-0.5 fill-current" />
                    </Button>
                </div>

                {/* Duration */}
                {video.duration && (
                    <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/60 backdrop-blur-sm rounded text-[10px] font-medium text-white flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {video.duration}
                    </div>
                )}
            </div>

            {/* ===================================================
                CONTENT
            =================================================== */}
            <CardContent className="p-4 flex-1">
                <h3 className="font-semibold leading-tight line-clamp-2 mb-2 group-hover:text-primary transition-colors">
                    {video.title}
                </h3>

                <div className="flex items-center justify-between text-xs text-muted-foreground">
                    {/* Views (Editor/Admin only) */}
                    {!isViewer && video.views && (
                        <div className="flex items-center gap-1">
                            <Eye className="h-3 w-3" />
                            <span>{video.views}</span>
                        </div>
                    )}

                    {/* Date */}
                    {video.date && (
                        <div className="flex items-center gap-1 ml-auto">
                            <Calendar className="h-3 w-3" />
                            <span>{video.date}</span>
                        </div>
                    )}
                </div>
            </CardContent>

            {/* ===================================================
                FOOTER / ACTIONS (Editor/Admin only)
            =================================================== */}
            {!isViewer && (
                <CardFooter className="p-2 pt-0 flex justify-end border-t bg-muted/20">
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0"
                                onClick={(e) => e.stopPropagation()}
                            >
                                <MoreVertical className="h-4 w-4" />
                            </Button>
                        </DropdownMenuTrigger>

                        <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={handleNavigate}>
                                Edit Details
                            </DropdownMenuItem>
                            <DropdownMenuItem>Download MP4</DropdownMenuItem>
                            <DropdownMenuItem className="text-red-500">
                                Delete
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </CardFooter>
            )}
        </Card>
    );
}
