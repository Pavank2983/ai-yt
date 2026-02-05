"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import {
    MoreHorizontal,
    FileText,
    Plus,
    Search,
    Clock,
    Play,
} from "lucide-react";

import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import StatusBadge, { StatusType } from "@/components/common/StatusBadge";

/* ===================================================
   TYPES (BACKEND-ALIGNED)
=================================================== */

type ScriptListItem = {
    id: number;
    title: string;
    excerpt: string;
    status: StatusType;
    scenes: number;
    updated: string; // already humanized
};

/* ===================================================
   API
=================================================== */

async function getScripts(): Promise<ScriptListItem[]> {
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/scripts`,
        { credentials: "include" }
    );

    if (!res.ok) {
        throw new Error("Failed to fetch scripts");
    }

    return res.json();
}

/* ===================================================
   PAGE
=================================================== */

export default function ScriptsPage() {
    const router = useRouter();
    const [search, setSearch] = useState("");

    const { data: scripts = [], isLoading } = useQuery({
        queryKey: ["scripts"],
        queryFn: getScripts,
    });

    const filteredScripts = useMemo(() => {
        if (!search.trim()) return scripts;

        const q = search.toLowerCase();

        return scripts.filter((script) =>
            script.title.toLowerCase().includes(q) ||
            (script.excerpt ?? "").toLowerCase().includes(q)
        );
    }, [scripts, search]);


    const goToNewScript = () => router.push("/dashboard/scripts/new");
    const goToScript = (id: number) => router.push(`/dashboard/scripts/${id}`);

    return (
        <div className="space-y-6">
            {/* ================= HEADER ================= */}
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">
                        My Scripts
                    </h2>
                    <p className="text-muted-foreground">
                        Write, generate, and manage AI video scripts.
                    </p>
                </div>

                <Button onClick={goToNewScript}>
                    <Plus className="mr-2 h-4 w-4" />
                    New Script
                </Button>
            </div>

            {/* ================= SEARCH ================= */}
            <div className="flex items-center py-4 bg-card p-4 rounded-lg border">
                <div className="relative w-full max-w-sm">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input placeholder="Search scripts..." className="pl-8" value={search} onChange={(e) => setSearch(e.target.value)} />
                </div>
            </div>

            {/* ================= TABLE ================= */}
            <div className="rounded-md border bg-card">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[420px]">
                                Script Details
                            </TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Scenes</TableHead>
                            <TableHead>Last Updated</TableHead>
                            <TableHead className="text-right">
                                Actions
                            </TableHead>
                        </TableRow>
                    </TableHeader>

                    <TableBody>
                        {/* LOADING */}
                        {isLoading && (
                            <TableRow>
                                <TableCell
                                    colSpan={5}
                                    className="text-center py-8 text-muted-foreground"
                                >
                                    Loading scripts…
                                </TableCell>
                            </TableRow>
                        )}

                        {/* EMPTY */}
                        {!isLoading && filteredScripts.length === 0 && (
                            <TableRow>
                                <TableCell
                                    colSpan={5}
                                    className="text-center py-8 text-muted-foreground"
                                >
                                    {search
                                        ? `No scripts found for "${search}"`
                                        : "No scripts yet. Create your first one 🚀"}
                                </TableCell>
                            </TableRow>
                        )}

                        {/* DATA */}
                        {filteredScripts.map((script) => {
                            const canGenerate =
                                script.status === "draft" &&
                                script.scenes > 0;

                            return (
                                <TableRow
                                    key={script.id}
                                    className="cursor-pointer hover:bg-muted/50 transition-colors"
                                    onClick={() =>
                                        goToScript(script.id)
                                    }
                                >
                                    {/* DETAILS */}
                                    <TableCell>
                                        <div className="flex items-start gap-3">
                                            <div className="h-10 w-10 rounded bg-primary/10 flex items-center justify-center text-primary shrink-0">
                                                <FileText className="h-5 w-5" />
                                            </div>

                                            <div>
                                                <div className="font-medium">
                                                    {script.title ||
                                                        "Untitled Script"}
                                                </div>
                                                <div className="text-xs text-muted-foreground line-clamp-1 max-w-[280px]">
                                                    {script.excerpt || "—"}
                                                </div>
                                            </div>
                                        </div>
                                    </TableCell>

                                    {/* STATUS */}
                                    <TableCell>
                                        <StatusBadge
                                            status={script.status}
                                            size="sm"
                                        />
                                    </TableCell>

                                    {/* SCENES */}
                                    <TableCell>
                                        <span className="font-medium">
                                            {script.scenes}
                                        </span>{" "}
                                        scenes
                                    </TableCell>

                                    {/* UPDATED */}
                                    <TableCell>
                                        <div className="flex items-center text-muted-foreground text-xs">
                                            <Clock className="h-3 w-3 mr-1" />
                                            {script.updated}
                                        </div>
                                    </TableCell>

                                    {/* ACTIONS */}
                                    <TableCell
                                        className="text-right"
                                        onClick={(e) =>
                                            e.stopPropagation()
                                        }
                                    >
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button
                                                    variant="ghost"
                                                    className="h-8 w-8 p-0"
                                                >
                                                    <MoreHorizontal className="h-4 w-4" />
                                                </Button>
                                            </DropdownMenuTrigger>

                                            <DropdownMenuContent align="end">
                                                <DropdownMenuItem
                                                    onClick={() =>
                                                        goToScript(
                                                            script.id
                                                        )
                                                    }
                                                >
                                                    Edit
                                                </DropdownMenuItem>

                                                {canGenerate && (
                                                    <DropdownMenuItem className="text-primary">
                                                        <Play className="h-4 w-4 mr-2" />
                                                        Generate Video
                                                    </DropdownMenuItem>
                                                )}

                                                <DropdownMenuItem className="text-red-500">
                                                    Delete
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
