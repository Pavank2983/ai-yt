"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

import {
    Save,
    Play,
    Wand2,
    Clock,
    ChevronLeft,
} from "lucide-react";

import { getScript, analyzeScript, generateVideo } from "@/lib/api/scripts";

/* ===================================================
   TYPES (BACKEND-ALIGNED)
=================================================== */

type Scene = {
    index: number;
    narration: string;
    duration_sec: number;
    emotion?: string;
    pacing?: string;
    visual_prompt?: string;
};

type ScriptResponse = {
    id: number;
    title: string;
    content: string;
    status: "draft" | "running" | "success";
    review_status: "pending" | "approved" | "rejected";
    can_edit: boolean;
    can_analyze: boolean;
    can_generate_video: boolean;
};

/* ===================================================
   UI HELPERS
=================================================== */

function CenteredMessage({
    title,
    description,
    loading,
    action,
}: {
    title: string;
    description?: string;
    loading?: boolean;
    action?: { label: string; onClick: () => void };
}) {
    return (
        <div className="flex flex-col items-center justify-center h-[60vh] text-center gap-3">
            <h2 className="text-lg font-semibold">{title}</h2>
            {description && (
                <p className="text-sm text-muted-foreground">
                    {description}
                </p>
            )}
            {loading && (
                <div className="animate-pulse text-xs text-muted-foreground">
                    Loading…
                </div>
            )}
            {action && (
                <Button size="sm" onClick={action.onClick}>
                    {action.label}
                </Button>
            )}
        </div>
    );
}

/* ===================================================
   PAGE
=================================================== */

export default function ScriptEditorPage() {
    const router = useRouter();
    const params = useParams();
    const scriptId = params?.id as string | undefined;

    /* -------------------------------
       STATE
    -------------------------------- */
    const [title, setTitle] = useState("");
    const [content, setContent] = useState("");
    const [scenes, setScenes] = useState<Scene[]>([]);

    /* -------------------------------
       QUERY (SCRIPT META)
    -------------------------------- */
    const {
        data,
        isLoading,
        isError,
        error,
        refetch,
    } = useQuery<ScriptResponse>({
        queryKey: ["script", scriptId],
        queryFn: () => {
            if (!scriptId) throw new Error("Script ID is missing");
            return getScript(scriptId);
        },
        enabled: !!scriptId,
        retry: (count, err) => {
            const status = err instanceof Error && "status" in err
                ? (err as Error & { status?: number }).status
                : undefined;
            return ![401, 403, 404].includes(status ?? 0) && count < 2;
        },
        refetchOnWindowFocus: false,
    });

    /* -------------------------------
       MUTATION (ANALYZE)
    -------------------------------- */
    const analyzeMutation = useMutation({
        mutationFn: () => {
            if (!scriptId) throw new Error("Script ID is missing");
            return analyzeScript(scriptId);
        },
        onSuccess: (res) => {
            setScenes(res.scenes || []);
        },
    });

    /* -------------------------------
        MUTATION (GENERATE VIDEO)
    -------------------------------- */
    const generateVideoMutation = useMutation({
        mutationFn: () => {
            if (!scriptId) throw new Error("Script ID is missing");
            return generateVideo(scriptId);
        },
        onSuccess: (res) => {
            // Redirect to video detail page
            if (res?.video_id) {
                router.push(`/dashboard/videos/${res.video_id}`);
            }
        },
    });

    /* -------------------------------
       SYNC DATA
    -------------------------------- */
    useEffect(() => {
        if (!data) return;
        const timer = window.setTimeout(() => {
            setTitle(data.title);
            setContent(data.content);
        }, 0);
        return () => window.clearTimeout(timer);
    }, [data]);

    if (!scriptId) {
        return (
            <CenteredMessage
                title="Invalid Script"
                description="Script ID is missing or invalid."
            />
        );
    }

    /* -------------------------------
       ERROR STATES
    -------------------------------- */
    if (isLoading) {
        return (
            <CenteredMessage
                title="Loading script…"
                loading
            />
        );
    }

    if (isError) {
        const status = error instanceof Error && "status" in error
            ? (error as Error & { status?: number }).status
            : undefined;

        if (status === 401)
            return <CenteredMessage title="Unauthorized" />;
        if (status === 403)
            return <CenteredMessage title="Access Denied" />;
        if (status === 404)
            return <CenteredMessage title="Script Not Found" />;

        return (
            <CenteredMessage
                title="Server Error"
                action={{ label: "Retry", onClick: refetch }}
            />
        );
    }

    if (!data) {
        return (
            <CenteredMessage
                title="No Data"
                description="Script data could not be loaded."
            />
        );
    }

    const {
        can_edit,
        can_analyze,
        can_generate_video,
    } = data;

    /* ===================================================
       RENDER
    =================================================== */

    return (
        <div className="h-[calc(100vh-5rem)] flex flex-col gap-4">
            {/* HEADER */}
            <div className="flex items-center justify-between border-b pb-4">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="sm" onClick={() => router.push("/dashboard/scripts")}>
                        <ChevronLeft className="h-4 w-4 mr-1" /> Back
                    </Button>

                    <Input
                        value={title}
                        disabled={!can_edit}
                        onChange={(e) => setTitle(e.target.value)}
                        className="text-lg font-bold border-none px-0 w-[320px]"
                    />
                </div>

                <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled={!can_edit}>
                        <Save className="h-4 w-4 mr-2" /> Save Draft
                    </Button>

                    <Button
                        size="sm"
                        disabled={generateVideoMutation.isPending}
                        onClick={() => generateVideoMutation.mutate()}
                    >
                        <Play className="h-4 w-4 mr-2" />
                        {generateVideoMutation.isPending ? "Starting…" : "Generate Video"}
                    </Button>

                </div>
            </div>

            {/* MAIN GRID */}
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-0">
                {/* SCRIPT */}
                <div className="flex flex-col">
                    <Label className="mb-2 text-muted-foreground">
                        Script Content
                    </Label>

                    <Card className="flex-1">
                        <CardContent className="p-0 flex flex-col h-full">
                            <Textarea
                                value={content}
                                disabled={!can_edit}
                                onChange={(e) => setContent(e.target.value)}
                                className="flex-1 resize-none p-6 font-mono text-sm"
                            />

                            <div className="p-2 border-t flex justify-between text-xs">
                                <span>{content.length} chars</span>

                                <Button
                                    variant="ghost"
                                    size="sm"
                                    disabled={!can_analyze || analyzeMutation.isPending}
                                    onClick={() => analyzeMutation.mutate()}
                                >
                                    <Wand2 className="h-3 w-3 mr-1" />
                                    {analyzeMutation.isPending
                                        ? "Analyzing…"
                                        : "Analyze & Split"}
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* SCENES */}
                <div className="flex flex-col">
                    <Label className="mb-2 text-muted-foreground">
                        Generated Scenes
                    </Label>

                    <Card className="flex-1">
                        <ScrollArea className="h-full">
                            <CardContent className="space-y-4 p-4">
                                {scenes.length === 0 && (
                                    <div className="text-center text-sm text-muted-foreground py-12">
                                        No scenes generated yet
                                    </div>
                                )}

                                {scenes.map((scene) => (
                                    <div
                                        key={scene.index}
                                        className="border rounded-md p-3 space-y-2"
                                    >
                                        <div className="flex justify-between text-xs text-muted-foreground">
                                            <span>Scene {scene.index}</span>
                                            <span className="flex items-center gap-1">
                                                <Clock className="h-3 w-3" />
                                                {scene.duration_sec}s
                                            </span>
                                        </div>

                                        <p className="text-sm font-medium">
                                            “{scene.narration}”
                                        </p>

                                        {scene.visual_prompt && (
                                            <p className="text-xs text-muted-foreground">
                                                🎥 {scene.visual_prompt}
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </CardContent>
                        </ScrollArea>
                    </Card>
                </div>
            </div>
        </div>
    );
}
