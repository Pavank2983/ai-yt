"use client";

import { useRouter } from "next/navigation";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    MoreHorizontal,
    FileText,
    Plus,
    Search,
    Clock,
} from "lucide-react";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// Mock Script Data
const SCRIPTS = [
    {
        id: "1",
        title: "The Rise of Artificial Intelligence",
        excerpt: "In the early 21st century, humanity faced a new dawn...",
        status: "completed",
        scenes: 12,
        updated: "2 days ago",
        author: "Demo User",
    },
    {
        id: "2",
        title: "5 Productivity Hacks for Developers",
        excerpt: "Are you tired of feeling overwhelmed by your code base?...",
        status: "draft",
        scenes: 5,
        updated: "4 hours ago",
        author: "Demo User",
    },
    {
        id: "3",
        title: "Why Mars is the Next Frontier",
        excerpt: "Looking up at the red planet, we see more than just rock...",
        status: "generating",
        scenes: 8,
        updated: "Just now",
        author: "Editor John",
    },
    {
        id: "4",
        title: "History of the Roman Empire Part 1",
        excerpt: "Rome wasn't built in a day, and neither was its fall...",
        status: "draft",
        scenes: 0,
        updated: "1 week ago",
        author: "Demo User",
    },
];

// Scripts Page
export default function ScriptsPage() {
    const router = useRouter();

    const goToNewScript = () => router.push("/dashboard/scripts/new");
    const goToScript = (id: string) => router.push(`/dashboard/scripts/${id}`);

    return (
        <div className="space-y-6">
            {/* HEADER */}
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">My Scripts</h2>
                    <p className="text-muted-foreground">
                        Write, edit, and manage your video scripts.
                    </p>
                </div>
                <Button onClick={goToNewScript}>
                    <Plus className="mr-2 h-4 w-4" /> New Script
                </Button>
            </div>

            {/* SEARCH BAR */}
            <div className="flex items-center py-4 bg-card p-4 rounded-lg border shadow-sm">
                <div className="relative w-full max-w-sm">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input placeholder="Search scripts..." className="pl-8" />
                </div>
            </div>

            {/* SCRIPTS TABLE */}
            <div className="rounded-md border bg-card shadow-sm">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[400px]">Script Details</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Scenes</TableHead>
                            <TableHead>Last Updated</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>

                    <TableBody>
                        {SCRIPTS.map((script) => (
                            <TableRow
                                key={script.id}
                                className="cursor-pointer hover:bg-muted/50 transition-colors"
                                onClick={() => goToScript(script.id)}
                            >
                                {/* DETAILS */}
                                <TableCell>
                                    <div className="flex items-start gap-3">
                                        <div className="h-10 w-10 rounded bg-primary/10 flex items-center justify-center text-primary shrink-0">
                                            <FileText className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <div className="font-medium">{script.title}</div>
                                            <div className="text-xs text-muted-foreground line-clamp-1 max-w-[250px]">
                                                {script.excerpt}
                                            </div>
                                        </div>
                                    </div>
                                </TableCell>

                                {/* STATUS */}
                                <TableCell>
                                    <Badge
                                        variant={
                                            script.status === "completed"
                                                ? "default"
                                                : script.status === "generating"
                                                    ? "secondary"
                                                    : "outline"
                                        }
                                        className="capitalize"
                                    >
                                        {script.status}
                                    </Badge>
                                </TableCell>

                                {/* SCENES */}
                                <TableCell>
                                    <div className="flex items-center text-muted-foreground text-sm">
                                        <span className="font-medium text-foreground mr-1">
                                            {script.scenes}
                                        </span>
                                        scenes
                                    </div>
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
                                    onClick={(e) => e.stopPropagation()} // Prevent parent click
                                >
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button variant="ghost" className="h-8 w-8 p-0">
                                                <MoreHorizontal className="h-4 w-4" />
                                            </Button>
                                        </DropdownMenuTrigger>

                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem
                                                onClick={() => goToScript(script.id)}
                                            >
                                                Edit
                                            </DropdownMenuItem>

                                            <DropdownMenuItem>Duplicate</DropdownMenuItem>

                                            <DropdownMenuItem className="text-red-500">
                                                Delete
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
