"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import MetricsCard from "@/components/dashboard/MetricsCard";
import VideoCard from "@/components/dashboard/VideoCard";
import { Button } from "@/components/ui/button";
import { Plus, ArrowRight, Activity, Video, Eye, Zap } from "lucide-react";

// ================================
// MOCK DATA (temporary)
// ================================

const MOCK_VIDEOS = [
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
];

export default function DashboardOverviewPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      {/* ================================
          HEADER
      ================================ */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>

          <p className="text-muted-foreground mt-1">
            Welcome back, {user?.name?.split(" ")[0] || "Creator"}.
            Here's what’s happening across your channels.
          </p>
        </div>

        <div className="flex gap-2">
          <Button>
            <Plus className="mr-2 h-4 w-4" /> New Video
          </Button>
        </div>
      </div>

      {/* ================================
          METRICS CARDS
      ================================ */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricsCard
          title="Total Videos"
          value="124"
          icon={Video}
          description="Videos created this month"
          trend="12%"
          trendUp={true}
        />

        <MetricsCard
          title="Total Views"
          value="45.2M"
          icon={Eye}
          description="Across all channels"
          trend="8.2%"
          trendUp={true}
        />

        <MetricsCard
          title="Active Jobs"
          value="3"
          icon={Activity}
          description="Currently processing"
          trend="Running"
          trendUp={true}
        />

        <MetricsCard
          title="Credits Left"
          value="850"
          icon={Zap}
          description="Renews in 12 days"
          trend="-150"
          trendUp={false}
        />
      </div>

      {/* ================================
          RECENT VIDEOS
      ================================ */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold">Recent Videos</h3>

          <Button variant="ghost" size="sm" asChild>
            <Link href="/dashboard/videos" className="flex items-center text-primary">
              View All <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {MOCK_VIDEOS.map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>
      </div>
    </div>
  );
}
