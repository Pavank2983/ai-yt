"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    Save,
    Play,
    Image as ImageIcon,
    Wand2,
    Mic,
    Clock,
    ChevronLeft,
    Plus,
} from "lucide-react";

interface ScriptEditorPageProps {
    params: { id: string };
}

// Mock Scenes
const MOCK_SCENES = [
    {
        id: 1,
        text: "In the early 21st century, humanity faced a new dawn of intelligence.",
        visual:
            "Futuristic city skyline with digital overlays, cinematic lighting, blue and purple neon.",
        duration: 5,
    },
    {
        id: 2,
        text: "Machines began to learn, not just calculate.",
        visual:
            "Close up of a robotic eye opening, revealing complex data streams within the iris.",
        duration: 4,
    },
    {
        id: 3,
        text: "This was the beginning of the AI revolution.",
        visual: "Abstract visualization of neural networks connecting across a globe.",
        duration: 6,
    },
];

export default function ScriptEditorPage({ params }: ScriptEditorPageProps) {
    const router = useRouter();
    const isNew = params.id === "new";

    const [title, setTitle] = useState(
        isNew ? "Untitled Script" : "The Rise of Artificial Intelligence"
    );

    const [scriptBody, setScriptBody] = useState(
        "In the early 21st century, humanity faced a new dawn of intelligence.\n\nMachines began to learn, not just calculate.\n\nThis was the beginning of the AI revolution."
    );

    const [scenes, setScenes] = useState(MOCK_SCENES);
    const [isGenerating, setIsGenerating] = useState(false);

    const goBack = () => router.push("/dashboard/scripts");

    const handleGenerateScenes = () => {
        setIsGenerating(true);
        setTimeout(() => {
            setIsGenerating(false);
            // Mock generation
        }, 2000);
    };

    return (
        <div className="h-[calc(100vh-5rem)] flex flex-col gap-4">
            {/* HEADER */}
            <div className="flex items-center justify-between border-b pb-4">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="sm" onClick={goBack}>
                        <ChevronLeft className="h-4 w-4 mr-1" /> Back
                    </Button>

                    <div className="h-6 w-[1px] bg-border" />

                    <Input
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="text-lg font-bold border-none shadow-none focus-visible:ring-0 px-0 w-[300px] h-auto"
                    />
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground mr-2">
                        Auto-saved 2m ago
                    </span>

                    <Button variant="outline" size="sm">
                        <Save className="h-4 w-4 mr-2" /> Save Draft
                    </Button>

                    <Button size="sm" className="bg-primary hover:bg-primary/90">
                        <Play className="h-4 w-4 mr-2" /> Generate Video
                    </Button>
                </div>
            </div>

            {/* MAIN EDITOR GRID */}
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-0">

                {/* LEFT SIDE — Script Text */}
                <div className="flex flex-col h-full">
                    <Label className="mb-2 font-medium text-muted-foreground">
                        Script Content
                    </Label>

                    <Card className="flex-1 border-border/50 shadow-sm">
                        <CardContent className="p-0 flex-1 flex flex-col">
                            <Textarea
                                value={scriptBody}
                                onChange={(e) => setScriptBody(e.target.value)}
                                className="flex-1 resize-none border-0 focus-visible:ring-0 p-6 text-base leading-relaxed font-mono"
                                placeholder="Start typing your script..."
                            />

                            {/* FOOTER BAR */}
                            <div className="p-2 border-t bg-muted/10 flex justify-between items-center text-xs text-muted-foreground">
                                <div className="flex gap-4">
                                    <span>{scriptBody.length} chars</span>
                                    <span>~{Math.ceil(scriptBody.length / 15)} sec duration</span>
                                </div>

                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 text-xs"
                                    onClick={handleGenerateScenes}
                                >
                                    <Wand2 className="h-3 w-3 mr-1" /> Analyze & Split
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* RIGHT SIDE — Scenes + Settings */}
                <div className="flex flex-col h-full min-h-0">
                    <Tabs defaultValue="scenes" className="flex-1 flex flex-col">
                        <div className="flex items-center justify-between mb-2">
                            <Label className="font-medium text-muted-foreground">
                                Output Config
                            </Label>

                            <TabsList className="h-8">
                                <TabsTrigger value="scenes" className="text-xs">
                                    Scenes
                                </TabsTrigger>
                                <TabsTrigger value="settings" className="text-xs">
                                    Settings
                                </TabsTrigger>
                            </TabsList>
                        </div>

                        {/* SCENES TAB */}
                        <TabsContent value="scenes" className="flex-1 min-h-0 mt-0">
                            <ScrollArea className="h-full pr-4">
                                <div className="space-y-4 pb-4">
                                    {scenes.map((scene, index) => (
                                        <Card
                                            key={scene.id}
                                            className="border-border/50 group hover:border-primary/30 transition-colors"
                                        >
                                            <CardContent className="p-4 space-y-3">
                                                {/* Header */}
                                                <div className="flex justify-between items-start">
                                                    <div className="flex items-center gap-2">
                                                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                                                            {index + 1}
                                                        </span>

                                                        <span className="text-xs text-muted-foreground font-mono flex items-center">
                                                            <Clock className="h-3 w-3 mr-1" />{" "}
                                                            {scene.duration}s
                                                        </span>
                                                    </div>

                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-6 w-6 opacity-0 group-hover:opacity-100"
                                                    >
                                                        <ImageIcon className="h-3 w-3" />
                                                    </Button>
                                                </div>

                                                {/* Script Text */}
                                                <p className="text-sm font-medium leading-snug">
                                                    "{scene.text}"
                                                </p>

                                                {/* Visual Prompt */}
                                                <div className="bg-muted/30 p-2 rounded border text-xs text-muted-foreground flex gap-2 items-start">
                                                    <Wand2 className="h-3 w-3 shrink-0 mt-0.5 text-primary" />
                                                    <span>Visual Prompt: {scene.visual}</span>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))}

                                    <Button
                                        variant="outline"
                                        className="w-full border-dashed border-2 h-12 text-muted-foreground hover:text-primary hover:border-primary/50"
                                    >
                                        <Plus className="h-4 w-4 mr-2" /> Add Scene Manually
                                    </Button>
                                </div>
                            </ScrollArea>
                        </TabsContent>

                        {/* SETTINGS TAB */}
                        <TabsContent value="settings" className="mt-0">
                            <Card>
                                <CardContent className="p-6 space-y-6">
                                    {/* Voice */}
                                    <div className="space-y-2">
                                        <Label>Voiceover</Label>
                                        <div className="flex gap-2 items-center p-3 border rounded-md cursor-pointer hover:border-primary transition-colors">
                                            <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-600">
                                                <Mic className="h-5 w-5" />
                                            </div>

                                            <div className="flex-1">
                                                <div className="font-medium text-sm">
                                                    Adam (Deep, Narrator)
                                                </div>
                                                <div className="text-xs text-muted-foreground">
                                                    English, Male, Serious
                                                </div>
                                            </div>

                                            <Button variant="ghost" size="sm">
                                                Change
                                            </Button>
                                        </div>
                                    </div>

                                    {/* Background Music */}
                                    <div className="space-y-2">
                                        <Label>Background Music</Label>
                                        <div className="flex gap-2 items-center p-3 border rounded-md cursor-pointer hover:border-primary transition-colors">
                                            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                                                <Play className="h-5 w-5" />
                                            </div>

                                            <div className="flex-1">
                                                <div className="font-medium text-sm">Cinematic Rise</div>
                                                <div className="text-xs text-muted-foreground">
                                                    Ambient, Suspense
                                                </div>
                                            </div>

                                            <Button variant="ghost" size="sm">
                                                Change
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </div>
    );
}
