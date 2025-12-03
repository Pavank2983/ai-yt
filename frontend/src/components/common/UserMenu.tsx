"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import useIsDashboard from "@/hooks/useIsDashboard";
import ThemeToggle from "./ThemeToggle";
import { useAuth } from "@/context/AuthContext";

type Props = {
    home?: boolean;
    className?: string;
};

export default function UserMenu({ home = false, className = "" }: Props) {
    const { user, loading, logout } = useAuth();
    const isDashboard = useIsDashboard();
    const router = useRouter();
    const [open, setOpen] = useState(false);
    const rootRef = useRef<HTMLDivElement | null>(null);

    // close menu on click outside
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, []);

    if (loading) return null;

    const go = (href: string) => {
        setOpen(false);
        router.push(href);
    };

    const handleLogout = async () => {
        await logout();
        setOpen(false);
        router.push("/");
    };

    return (
        <div ref={rootRef} className={`relative inline-block ${className}`}>

            {/* TOP BUTTON */}
            <button
                onClick={() => setOpen((s) => !s)}
                className="
                    flex items-center gap-2
                    px-3 py-1.5
                    rounded-full
                    bg-[#111520]
                    border border-white/10
                    hover:bg-[#1a1f2d]
                    transition
                "
            >
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-purple-500 to-fuchsia-500 flex items-center justify-center text-white font-semibold">
                    {user?.name?.charAt(0).toUpperCase()}
                </div>

                <span className="hidden sm:block text-sm font-medium text-white/90">
                    {user?.name}
                </span>

                <svg className="h-4 w-4 text-white/70" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd"
                        d="M5.23 7.21a.75.75 0 011.06 0L10 10.92l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.24a.75.75 0 01-1.06 0L5.23 8.27a.75.75 0 010-1.06z"
                        clipRule="evenodd"
                    />
                </svg>
            </button>

            {/* DROPDOWN */}
            {open && (
                <div
                    className="
                        absolute right-0 mt-3 w-72 z-50
                        bg-[#0D1117]
                        border border-white/10
                        rounded-2xl
                        shadow-[0_4px_30px_rgba(0,0,0,0.4)]
                        overflow-hidden
                        animate-scaleFade
                    "
                >
                    {/* Profile Header */}
                    <div className="flex items-center gap-3 p-4">
                        <div className="h-12 w-12 rounded-full bg-gradient-to-br from-purple-500 to-fuchsia-500 flex items-center justify-center text-white text-lg font-semibold">
                            {user?.name?.charAt(0).toUpperCase()}
                        </div>

                        <div>
                            <div className="text-white font-medium text-sm">{user?.name}</div>
                            <div className="text-white/60 text-xs">{user?.email}</div>
                        </div>
                    </div>

                    {/* Divider */}
                    <div className="h-px bg-white/10" />

                    {/* Quick actions */}
                    <div className="flex items-center justify-between px-4 py-2 hover:bg-white/5 hover:text-white transition">
                        {!home && isDashboard && <ThemeToggle />}
                        <button
                            onClick={() => go("/profile")}
                            className="text-sm text-white/80 hover:text-white transition w-full text-left"
                        >
                            View Profile
                        </button>
                    </div>

                    {/* Divider */}
                    <div className="h-px bg-white/10" />

                    {/* Dashboard */}
                    <button
                        onClick={() => go("/dashboard")}
                        className="
                            w-full text-left px-4 py-3
                            text-sm text-white/90
                            hover:bg-white/5 hover:text-white
                            transition
                        "
                    >
                        Dashboard
                    </button>

                    {/* Logout */}
                    <button
                        onClick={handleLogout}
                        className="
                            w-full text-left px-4 py-3
                            text-sm text-red-400
                            hover:bg-[#CC0000] hover:text-white
                            transition
                        "
                    >
                        Log Out
                    </button>
                </div>
            )}
        </div>
    );
}
