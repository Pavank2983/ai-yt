"use client";

import Link from "next/link";
import { Bell, Search, Menu } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import UserMenu from "@/components/common/UserMenu";
import ThemeToggle from "@/components/common/ThemeToggle";
import { useAuth } from "@/context/AuthContext";

export default function Topbar({
    onMenuClick,
}: {
    onMenuClick: () => void;
}) {
    const { user } = useAuth();
    const isViewer = user?.role === "viewer";

    return (
        <header
            className="
                sticky top-0 z-30 flex h-16 w-full items-center
                justify-between border-b border-border
                bg-background/80 backdrop-blur-md
                px-4 md:px-6
            "
        >
            {/* ========== MOBILE MENU BUTTON ========== */}
            <div className="flex items-center gap-4 md:hidden">
                <Button variant="ghost" size="icon" onClick={onMenuClick}>
                    <Menu className="h-5 w-5" />
                </Button>
            </div>

            {/* ========== SEARCH BAR (Desktop Only) ========== */}
            <div className="hidden md:flex items-center w-full max-w-md">
                <div className="relative w-full">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        type="search"
                        placeholder={
                            isViewer
                                ? "Search videos..."
                                : "Search projects, scripts, or assets..."
                        }
                        className="
                            h-9 w-full rounded-md border border-input bg-background
                            pl-10 pr-3 text-sm shadow-sm placeholder:text-muted-foreground
                            focus-visible:ring-1 focus-visible:ring-primary/40
                            md:w-[300px] lg:w-[400px]
                        "
                    />
                </div>
            </div>

            {/* ========== RIGHT SIDE ACTIONS ========== */}
            <div className="flex items-center gap-2 md:gap-4">
                {/* Notifications (NOT for Viewer) */}
                {!isViewer && (
                    <Link href="/dashboard/notifications">
                        <Button
                            variant="ghost"
                            size="icon"
                            className="relative"
                        >
                            <Bell className="h-5 w-5 text-muted-foreground" />
                            <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-primary" />
                        </Button>
                    </Link>
                )}

                {/* Theme Toggle */}
                <ThemeToggle />

                {/* Divider */}
                <div className="h-8 w-[1px] bg-border mx-1" />

                {/* User Menu */}
                <UserMenu />
            </div>
        </header>
    );
}
