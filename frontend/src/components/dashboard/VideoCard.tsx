"use client";

import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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

export type VideoStatus = "completed" | "processing" | "draft" | "failed";

export interface VideoCardProps {
    video: {
        id: string | number;
        title: string;
        thumbnail?: string | null;
        status: VideoStatus;
        views?: string | number;
        duration?: string | null;
        date?: string | null;
    };
}

export default function VideoCard({ video }: VideoCardProps) {
    const router = useRouter();

    const statusColors: Record<VideoStatus, string> = {
        completed:
            "bg-green-500/15 text-green-600 dark:text-green-400 hover:bg-green-500/25 border-green-500/20",
        processing:
            "bg-blue-500/15 text-blue-600 dark:text-blue-400 hover:bg-blue-500/25 border-blue-500/20",
        draft:
            "bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 hover:bg-yellow-500/25 border-yellow-500/20",
        failed:
            "bg-red-500/15 text-red-600 dark:text-red-400 hover:bg-red-500/25 border-red-500/20",
    };

    const goToVideo = () => router.push(`/dashboard/videos/${video.id}`);

    return (
        <Card className="group overflow-hidden border-border/50 hover:border-primary/50 transition-all duration-300 flex flex-col h-full">

            {/* Thumbnail */}
            <div className="relative aspect-[9/16] bg-muted overflow-hidden">

                {video.thumbnail ? (
                    <Image
                        src={video.thumbnail}
                        alt={video.title}
                        fill
                        className="object-cover transition-transform duration-500 group-hover:scale-105"
                        unoptimized
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center bg-muted/50">
                        <Play className="h-12 w-12 text-muted-foreground/30" />
                    </div>
                )}

                {/* Hover Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

                {/* Status Badge */}
                <div className="absolute top-2 right-2">
                    <Badge
                        variant="outline"
                        className={cn(
                            "capitalize border backdrop-blur-sm",
                            statusColors[video.status]
                        )}
                    >
                        {video.status}
                    </Badge>
                </div>

                {/* Play Button */}
                <div className="absolute bottom-3 right-3 opacity-0 translate-y-2 transition-all duration-300 group-hover:opacity-100 group-hover:translate-y-0">
                    <Button
                        size="icon"
                        className="rounded-full h-10 w-10 bg-white text-black hover:bg-white/90 shadow-lg"
                        onClick={goToVideo}
                    >
                        <Play className="h-4 w-4 ml-0.5 fill-current" />
                    </Button>
                </div>

                {/* Duration */}
                <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/60 backdrop-blur-sm rounded text-[10px] font-medium text-white flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {video.duration || "-"}
                </div>
            </div>

            {/* Content */}
            <CardContent className="p-4 flex-1">
                <h3 className="font-semibold leading-tight line-clamp-2 mb-2 group-hover:text-primary transition-colors">
                    {video.title}
                </h3>

                <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                        <Eye className="h-3 w-3" />
                        <span>{video.views ?? "-"}</span>
                    </div>

                    <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>{video.date ?? "-"}</span>
                    </div>
                </div>
            </CardContent>

            {/* Footer / Menu */}
            <CardFooter className="p-2 pt-0 flex justify-end border-t bg-muted/20">
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <MoreVertical className="h-4 w-4" />
                        </Button>
                    </DropdownMenuTrigger>

                    <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={goToVideo}>Edit Details</DropdownMenuItem>
                        <DropdownMenuItem>Download MP4</DropdownMenuItem>
                        <DropdownMenuItem className="text-red-500">Delete</DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </CardFooter>
        </Card>
    );
}
