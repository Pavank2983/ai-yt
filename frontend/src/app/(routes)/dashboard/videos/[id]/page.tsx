"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { useAuth } from "@/context/AuthContext";
import Image from "next/image";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import StatusBadge, { normalizeStatus } from "@/components/common/StatusBadge";

import {
  Play,
  Share2,
  Download,
  ChevronLeft,
} from "lucide-react";

import {
  getDashboardVideos,
  approveDashboardVideo,
  rejectDashboardVideo,
} from "@/lib/api/dashboard";

import type { DashboardVideo } from "@/types/dashboard";

interface VideoDetailPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function VideoDetailPage({ params }: VideoDetailPageProps) {
  /* =========================
     ALL HOOKS FIRST (NO RETURNS)
  ========================= */

  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { id } = use(params);

  const isAdmin = user?.role === "admin";

  const { data: videos, isLoading } = useQuery<DashboardVideo[]>({
    queryKey: ["dashboard-videos"],
    queryFn: getDashboardVideos,
  });

  const video = videos?.find((v) => String(v.id) === id);
  const videoId = video ? Number(video.id) : null;

  const approveMutation = useMutation({
    mutationFn: () => {
      if (videoId === null) throw new Error("Video is not loaded");
      return approveDashboardVideo(videoId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard-videos"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => {
      if (videoId === null) throw new Error("Video is not loaded");
      return rejectDashboardVideo(videoId, "Rejected by admin");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard-videos"] });
    },
  });

  /* =========================
     SAFE CONDITIONAL RENDERING
  ========================= */

  if (!user) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="py-24 text-center text-muted-foreground">
        Loading video…
      </div>
    );
  }

  if (!video) {
    return (
      <div className="py-24 text-center text-muted-foreground">
        Video not found
      </div>
    );
  }

  /* =========================
     STATUS NORMALIZATION
  ========================= */

  const approvalStatus = normalizeStatus(video.approval_status ?? "pending_review");

  const canApprove =
    isAdmin &&
    video.status === "ready_for_review" &&
    approvalStatus !== "approved";

  /* =========================
     RENDER
  ========================= */

  return (
    <div className="space-y-6 pb-10">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push("/dashboard/videos")}
      >
        <ChevronLeft className="h-4 w-4 mr-1" /> Back to Videos
      </Button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* LEFT */}
        <div className="lg:col-span-2 space-y-6">
          <div className="aspect-video bg-black rounded-xl overflow-hidden relative border">
            {video.thumbnail_url && (
              <Image
                src={video.thumbnail_url}
                alt={video.title ?? "Video"}
                fill
                className="object-cover opacity-40"
                unoptimized
              />
            )}

            <div className="absolute inset-0 flex items-center justify-center">
              <div className="h-16 w-16 rounded-full bg-white/10 backdrop-blur flex items-center justify-center">
                <Play className="h-8 w-8 text-white ml-1" />
              </div>
            </div>
          </div>

          <h1 className="text-2xl font-bold">
            {video.title || "Untitled Video"}
          </h1>

          <div className="flex items-center gap-2">
            <StatusBadge status={normalizeStatus(video.status)} />
            <StatusBadge status={approvalStatus} />
          </div>

          <Separator />
        </div>

        {/* RIGHT */}
        <div className="space-y-6">
          {isAdmin && (
            <Card>
              <CardHeader>
                <CardTitle>Approval</CardTitle>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="flex justify-between text-sm items-center">
                  <span className="text-muted-foreground">
                    Approval Status
                  </span>
                  <StatusBadge status={approvalStatus} size="sm" />
                </div>

                {canApprove ? (
                  <div className="flex gap-2">
                    <Button
                      className="flex-1"
                      onClick={() => approveMutation.mutate()}
                      disabled={approveMutation.isPending}
                    >
                      Approve
                    </Button>

                    <Button
                      variant="destructive"
                      className="flex-1"
                      onClick={() => rejectMutation.mutate()}
                      disabled={rejectMutation.isPending}
                    >
                      Reject
                    </Button>
                  </div>
                ) : (
                  <div className="text-xs text-muted-foreground text-center">
                    No approval action available
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Video Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Label>Title</Label>
              <Input value={video.title ?? ""} disabled />
              <Label>Description</Label>
              <Textarea disabled value="Metadata editing coming soon" />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
