"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import AppLogo, { AppLogoSvg } from "@/components/common/AppLogo";

import {
    LayoutDashboard,
    Video,
    FileText,
    Mic,
    Users,
    Settings,
    CreditCard,
    BarChart3,
    YoutubeIcon,
    FolderOpen,
    Bell,
    ChevronLeft,
    ChevronRight,
    PlusCircle,
    Briefcase,
} from "lucide-react";
import { Button } from "@/components/ui/button";

/* ================================
   NAVIGATION ITEMS (ROLE-BASED)
================================ */
const NAV_ITEMS = [
    // ----- Viewer -----
    {
        title: "Overview",
        href: "/dashboard",
        icon: LayoutDashboard,
        roles: ["viewer", "editor", "admin"],
    },
    {
        title: "Videos",
        href: "/dashboard/videos",
        icon: Video,
        roles: ["viewer", "editor", "admin"],
    },
    {
        title: "Channels",
        href: "/dashboard/channels",
        icon: YoutubeIcon,
        roles: ["viewer", "editor", "admin"],
    },
    {
        title: "Profile",
        href: "/dashboard/profile",
        icon: Settings,
        roles: ["viewer", "editor", "admin"],
    },

    // ----- Editor -----
    {
        title: "My Scripts",
        href: "/dashboard/scripts",
        icon: FileText,
        roles: ["editor", "admin"],
    },
    {
        title: "My Voices",
        href: "/dashboard/voices",
        icon: Mic,
        roles: ["editor", "admin"],
    },
    {
        title: "My Videos",
        href: "/dashboard/my-videos",
        icon: Video,
        roles: ["editor", "admin"],
    },
    {
        title: "My Jobs",
        href: "/dashboard/my-jobs",
        icon: Briefcase,
        roles: ["editor", "admin"],
    },
    {
        title: "Assets",
        href: "/dashboard/assets",
        icon: FolderOpen,
        roles: ["editor", "admin"],
    },
    {
        title: "Preview Tools",
        href: "/dashboard/preview-tools",
        icon: Bell,
        roles: ["editor", "admin"],
    },

    // ----- Admin -----
    {
        title: "Users",
        href: "/dashboard/users",
        icon: Users,
        roles: ["admin"],
    },
    {
        title: "Team",
        href: "/dashboard/team",
        icon: Users,
        roles: ["admin"],
    },
    {
        title: "Analytics",
        href: "/dashboard/analytics",
        icon: BarChart3,
        roles: ["admin"],
    },
    {
        title: "Billing",
        href: "/dashboard/billing",
        icon: CreditCard,
        roles: ["admin"],
    },
    {
        title: "All Jobs",
        href: "/dashboard/jobs",
        icon: Briefcase,
        roles: ["admin"],
    },
];

/* ================================
   SIDEBAR COMPONENT
================================ */
export function Sidebar({
    isOpen,
    toggle,
}: {
    isOpen: boolean;
    toggle: () => void;
}) {
    const { user } = useAuth();
    const pathname = usePathname();

    const role = user?.role ?? "viewer";

    // 🔒 Role-based filtering (Viewer is minimal by design)
    const filteredNav = NAV_ITEMS.filter((item) =>
        item.roles.includes(role)
    );

    return (
        <motion.aside
            initial={false}
            animate={{ width: isOpen ? 240 : 72 }}
            className="
                fixed left-0 top-0 z-40 h-screen
                border-r border-border
                bg-card/80 backdrop-blur-xl
                transition-all duration-300
                flex flex-col
            "
        >
            {/* ---- Logo Header ---- */}
            <div className="flex h-16 items-center justify-between px-4 border-b border-border">
                <div
                    className={cn(
                        "flex items-center gap-2 overflow-hidden",
                        !isOpen && "justify-center w-full"
                    )}
                >
                    {!isOpen && <AppLogoSvg />}
                    {isOpen && <AppLogo />}
                </div>
            </div>

            {/* ---- Navigation ---- */}
            <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
                {filteredNav.map((item) => {
                    const isActive = pathname === item.href;

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                                "hover:bg-accent hover:text-accent-foreground",
                                isActive
                                    ? "bg-primary/10 text-primary hover:bg-primary/15 hover:text-primary"
                                    : "text-muted-foreground",
                                !isOpen && "justify-center px-2"
                            )}
                        >
                            <item.icon
                                className={cn(
                                    "h-5 w-5",
                                    isActive && "text-primary"
                                )}
                            />
                            {isOpen && <span>{item.title}</span>}

                            {/* Tooltip when collapsed */}
                            {!isOpen && isActive && (
                                <div
                                    className="
                                        absolute left-16 rounded-md bg-popover px-2 py-1 text-xs
                                        font-medium shadow-md
                                        animate-in fade-in-0 zoom-in-95
                                    "
                                >
                                    {item.title}
                                </div>
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* ---- Collapse Button ---- */}
            <div className="border-t border-border p-2">
                <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-center"
                    onClick={toggle}
                >
                    {isOpen ? (
                        <ChevronLeft className="h-4 w-4" />
                    ) : (
                        <ChevronRight className="h-4 w-4" />
                    )}
                </Button>
            </div>
        </motion.aside>
    );
}
