"use client";

import { useState } from "react";
import VideoCard from "@/components/dashboard/VideoCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Search, Filter, Plus, Video as VideoIcon } from "lucide-react";

// ================================
// MOCK VIDEO DATA
// ================================
const ALL_VIDEOS = [
    {
        id: "1",
        title: "Top 10 AI Tools You Need in 2024",
        thumbnail:
            "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400&h=700&fit=crop&q=80",
        status: "completed",
        views: "12.5K",
        duration: "0:58",
        date: "2 hrs ago",
    },
    {
        id: "2",
        title: "How to Automate Your Life with Python",
        thumbnail:
            "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=400&h=700&fit=crop&q=80",
        status: "processing",
        views: "0",
        duration: "0:45",
        date: "Just now",
    },
    {
        id: "3",
        title: "The Future of Space Travel Explained",
        thumbnail:
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400&h=700&fit=crop&q=80",
        status: "completed",
        views: "45.2K",
        duration: "0:59",
        date: "1 day ago",
    },
    {
        id: "4",
        title: "Secret History of Ancient Rome",
        thumbnail: null,
        status: "draft",
        views: "-",
        duration: "-",
        date: "Draft",
    },
    {
        id: "5",
        title: "Mind-Blowing Science Facts",
        thumbnail:
            "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=400&h=700&fit=crop&q=80",
        status: "failed",
        views: "-",
        duration: "0:30",
        date: "2 days ago",
    },
    {
        id: "6",
        title: "Easy Cooking Hacks for Beginners",
        thumbnail:
            "https://images.unsplash.com/photo-1556910103-1c02745a30bf?w=400&h=700&fit=crop&q=80",
        status: "completed",
        views: "2.1K",
        duration: "0:42",
        date: "3 days ago",
    },
];

// ================================
// VIDEOS PAGE (Next.js)
// ================================
export default function VideosPage() {
    const [filter, setFilter] = useState("all");

    const filteredVideos = ALL_VIDEOS.filter((v) =>
        filter === "all" ? true : v.status === filter
    );

    return (
        <div className="space-y-6">
            {/* ------------------------------------- */}
            {/* HEADER */}
            {/* ------------------------------------- */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Videos</h2>
                    <p className="text-muted-foreground">
                        Manage and track your AI-generated shorts.
                    </p>
                </div>

                <Button>
                    <Plus className="mr-2 h-4 w-4" /> Create New
                </Button>
            </div>

            {/* ------------------------------------- */}
            {/* FILTER BAR */}
            {/* ------------------------------------- */}
            <div className="flex flex-col sm:flex-row gap-4 justify-between items-center bg-muted/30 p-4 rounded-lg border">
                {/* Search */}
                <div className="flex items-center gap-2 w-full sm:w-auto">
                    <div className="relative w-full sm:w-64">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input placeholder="Search videos..." className="pl-8 bg-background" />
                    </div>

                    {/* Filter Button (future use) */}
                    <Button variant="outline" size="icon">
                        <Filter className="h-4 w-4" />
                    </Button>
                </div>

                {/* Tabs */}
                <Tabs defaultValue="all" className="w-full sm:w-auto" onValueChange={setFilter}>
                    <TabsList>
                        <TabsTrigger value="all">All</TabsTrigger>
                        <TabsTrigger value="completed">Published</TabsTrigger>
                        <TabsTrigger value="processing">Processing</TabsTrigger>
                        <TabsTrigger value="draft">Drafts</TabsTrigger>
                    </TabsList>
                </Tabs>
            </div>

            {/* ------------------------------------- */}
            {/* VIDEO GRID */}
            {/* ------------------------------------- */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                {filteredVideos.map((video) => (
                    <VideoCard key={video.id} video={video} />
                ))}

                {/* No Results State */}
                {filteredVideos.length === 0 && (
                    <div className="col-span-full flex flex-col items-center justify-center py-20 text-center">
                        <div className="h-20 w-20 rounded-full bg-muted flex items-center justify-center mb-4">
                            <VideoIcon className="h-10 w-10 text-muted-foreground" />
                        </div>
                        <h3 className="text-lg font-semibold">No videos found</h3>
                        <p className="text-muted-foreground max-w-sm mt-2">
                            Try adjusting your filters or search query, or create a new video to get started.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
