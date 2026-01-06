"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/context/AuthContext";

import VideoCard from "@/components/dashboard/VideoCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { Search, Filter, Plus, Video as VideoIcon } from "lucide-react";

import { getDashboardVideos } from "@/lib/api/dashboard";
import type { DashboardVideo } from "@/types/dashboard";

export default function DashboardVideosPage() {
    const { user } = useAuth();
    if (!user) return null;

    const isViewer = user.role === "viewer";

    const [search, setSearch] = useState("");
    const [filter, setFilter] = useState("all");

    const { data: videos = [], isLoading } = useQuery<DashboardVideo[]>({
        queryKey: ["dashboard-videos"],
        queryFn: getDashboardVideos,
    });

    /* =========================
       ROLE VISIBILITY
    ========================= */

    let visibleVideos = isViewer
        ? videos.filter((v) => v.status === "uploaded")
        : videos;

    /* =========================
       STATUS FILTER
    ========================= */

    if (filter !== "all") {
        visibleVideos = visibleVideos.filter(
            (v) => v.status === filter
        );
    }

    /* =========================
       SEARCH FILTER
    ========================= */

    if (search.trim()) {
        const q = search.toLowerCase();
        visibleVideos = visibleVideos.filter((v) =>
            v.title?.toLowerCase().includes(q)
        );
    }

    return (
        <div className="space-y-6">
            {/* ================= HEADER ================= */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Videos</h2>
                    <p className="text-muted-foreground">
                        Manage and track your AI-generated shorts.
                    </p>
                </div>

                {!isViewer && (
                    <Button>
                        <Plus className="mr-2 h-4 w-4" /> Create New
                    </Button>
                )}
            </div>

            {/* ================= FILTER BAR ================= */}
            <div className="flex flex-col sm:flex-row gap-4 justify-between items-center bg-muted/30 p-4 rounded-lg border">
                {/* Search */}
                <div className="flex items-center gap-2 w-full sm:w-auto">
                    <div className="relative w-full sm:w-64">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search videos..."
                            className="pl-8 bg-background"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>

                    <Button variant="outline" size="icon">
                        <Filter className="h-4 w-4" />
                    </Button>
                </div>

                {/* Tabs */}
                <Tabs
                    defaultValue="all"
                    className="w-full sm:w-auto"
                    onValueChange={setFilter}
                >
                    <TabsList>
                        <TabsTrigger value="all">All</TabsTrigger>
                        <TabsTrigger value="uploaded">Published</TabsTrigger>
                        <TabsTrigger value="rendering">Rendering</TabsTrigger>
                        <TabsTrigger value="draft">Drafts</TabsTrigger>
                        <TabsTrigger value="failed">Failed</TabsTrigger>
                    </TabsList>
                </Tabs>
            </div>

            {/* ================= VIDEO GRID ================= */}
            {isLoading ? (
                <div className="py-24 text-center text-muted-foreground">
                    Loading videos…
                </div>
            ) : visibleVideos.length === 0 ? (
                <div className="col-span-full flex flex-col items-center justify-center py-20 text-center">
                    <div className="h-20 w-20 rounded-full bg-muted flex items-center justify-center mb-4">
                        <VideoIcon className="h-10 w-10 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold">No videos found</h3>
                    <p className="text-muted-foreground max-w-sm mt-2">
                        Try adjusting your filters or search query.
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                    {visibleVideos.map((video) => (
                        <VideoCard key={video.id} video={video} />
                    ))}
                </div>
            )}
        </div>
    );
}
