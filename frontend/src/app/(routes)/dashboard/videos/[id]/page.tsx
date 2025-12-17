"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Play,
    Share2,
    Download,
    ThumbsUp,
    MessageSquare,
    Clock,
    ChevronLeft,
} from "lucide-react";
import Image from "next/image";

interface VideoDetailPageProps {
    params: {
        id: string;
    };
}

export default function VideoDetailPage({ params }: VideoDetailPageProps) {
    const router = useRouter();
    const { id } = params;

    // Mock data for now — will be replaced by API
    const MOCK_VIDEO = {
        id,
        title: "Top 10 AI Tools You Need in 2024",
        views: "12.5K",
        engagement: "98%",
        comments: 45,
        status: "published",
        uploaded: "2 hours ago",
        thumbnail:
            "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&h=1400&fit=crop&q=80",
        description:
            "In this video, we explore the best AI tools that will skyrocket your productivity...",
        tags: ["#AI", "#Tech", "#Productivity", "#Future"],
        resolution: "1080x1920 (9:16)",
        format: "MP4 (H.264)",
        size: "45.2 MB",
        voice: "Adam_v2",
    };

    return (
        <div className="space-y-6 pb-10">
            {/* Back Button */}
            <div className="flex items-center gap-4 mb-4">
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push("/dashboard/videos")}
                >
                    <ChevronLeft className="h-4 w-4 mr-1" /> Back to Videos
                </Button>
            </div>

            {/* MAIN GRID */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* LEFT COLUMN — VIDEO PLAYER + INSIGHTS */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Player */}
                    <div className="aspect-video bg-black rounded-xl overflow-hidden relative group shadow-2xl border border-white/10">
                        {/* Thumbnail */}
                        {MOCK_VIDEO.thumbnail ? (
                            <Image
                                src={MOCK_VIDEO.thumbnail}
                                alt={MOCK_VIDEO.title}
                                fill
                                className="object-cover opacity-40"
                                unoptimized
                            />
                        ) : null}

                        {/* Play Button */}
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="h-16 w-16 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center group-hover:scale-110 transition-transform cursor-pointer">
                                <Play className="h-8 w-8 text-white fill-white ml-1" />
                            </div>
                        </div>

                        {/* Video Info Overlay */}
                        <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
                            <div className="flex items-center justify-between text-white text-sm font-medium">
                                <span>0:00 / 0:58</span>
                                <span>1080p</span>
                            </div>
                        </div>
                    </div>

                    {/* TEXT + METADATA */}
                    <div className="space-y-4">
                        {/* Title & Actions */}
                        <div className="flex justify-between items-start">
                            <div>
                                <h1 className="text-2xl font-bold">{MOCK_VIDEO.title}</h1>
                                <div className="flex items-center gap-2 mt-2">
                                    <Badge
                                        variant="secondary"
                                        className="text-green-500 bg-green-500/10 border-green-500/20"
                                    >
                                        Published
                                    </Badge>
                                    <span className="text-sm text-muted-foreground">
                                        • Uploaded {MOCK_VIDEO.uploaded}
                                    </span>
                                </div>
                            </div>

                            <div className="flex gap-2">
                                <Button variant="outline" size="sm">
                                    <Share2 className="h-4 w-4 mr-2" />
                                    Share
                                </Button>
                                <Button size="sm">
                                    <Download className="h-4 w-4 mr-2" />
                                    Download
                                </Button>
                            </div>
                        </div>

                        <Separator />

                        {/* Stats */}
                        <div className="grid grid-cols-3 gap-4 text-center">
                            <div className="p-4 rounded-lg bg-card border">
                                <div className="text-2xl font-bold">{MOCK_VIDEO.views}</div>
                                <div className="text-xs text-muted-foreground uppercase font-medium mt-1">
                                    Views
                                </div>
                            </div>

                            <div className="p-4 rounded-lg bg-card border">
                                <div className="text-2xl font-bold flex items-center justify-center gap-2">
                                    {MOCK_VIDEO.engagement}
                                    <ThumbsUp className="h-4 w-4 text-green-500" />
                                </div>
                                <div className="text-xs text-muted-foreground uppercase font-medium mt-1">
                                    Engagement
                                </div>
                            </div>

                            <div className="p-4 rounded-lg bg-card border">
                                <div className="text-2xl font-bold">{MOCK_VIDEO.comments}</div>
                                <div className="text-xs text-muted-foreground uppercase font-medium mt-1">
                                    Comments
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* RIGHT COLUMN — METADATA FOR EDITING */}
                <div className="space-y-6">
                    {/* Metadata Editor */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Video Metadata</CardTitle>
                        </CardHeader>

                        <CardContent className="space-y-4">
                            {/* Title */}
                            <div className="space-y-2">
                                <Label>Title</Label>
                                <Input defaultValue={MOCK_VIDEO.title} />
                            </div>

                            {/* Description */}
                            <div className="space-y-2">
                                <Label>Description</Label>
                                <Textarea
                                    defaultValue={MOCK_VIDEO.description}
                                    className="min-h-[150px]"
                                />
                            </div>

                            {/* Tags */}
                            <div className="space-y-2">
                                <Label>Tags</Label>
                                <div className="flex flex-wrap gap-2 p-2 border rounded-md bg-background min-h-[40px]">
                                    {MOCK_VIDEO.tags.map((tag) => (
                                        <Badge
                                            key={tag}
                                            variant="secondary"
                                            className="rounded-sm px-1 font-normal"
                                        >
                                            {tag}
                                        </Badge>
                                    ))}
                                </div>
                            </div>

                            <Button className="w-full">Save Changes</Button>
                        </CardContent>
                    </Card>

                    {/* Technical Info */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Technical Details</CardTitle>
                        </CardHeader>

                        <CardContent className="space-y-2 text-sm">
                            <div className="flex justify-between py-1 border-b border-border/50">
                                <span className="text-muted-foreground">Resolution</span>
                                <span>{MOCK_VIDEO.resolution}</span>
                            </div>

                            <div className="flex justify-between py-1 border-b border-border/50">
                                <span className="text-muted-foreground">Format</span>
                                <span>{MOCK_VIDEO.format}</span>
                            </div>

                            <div className="flex justify-between py-1 border-b border-border/50">
                                <span className="text-muted-foreground">Size</span>
                                <span>{MOCK_VIDEO.size}</span>
                            </div>

                            <div className="flex justify-between py-1 pt-2">
                                <span className="text-muted-foreground">Voice ID</span>
                                <span>{MOCK_VIDEO.voice}</span>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
