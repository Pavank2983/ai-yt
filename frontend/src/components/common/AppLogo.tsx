"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";

interface AppLogoProps {
    size?: number;              // width/height of the logo square
    showText?: boolean;         // toggle "AI Shorts" label
    className?: string;         // custom wrapper styles
    href?: string;              // link destination (default: "/")
    svgClassName?: string;      // custom SVG styles
}

export default function AppLogo({
    size = 40,
    showText = true,
    className = "",
    href = "/",
    svgClassName = "w-6 h-6 text-white",
}: AppLogoProps) {
    return (
        <Link href={href} className={cn("flex items-center gap-2", className)}>
            {/* Logo Icon */}
            <div
                className={cn(
                    "rounded-xl bg-gradient-to-br logo-icon-bg  from-primary  to-accent flex items-center justify-center",
                )}
                style={{ width: size, height: size }}
            >
                <svg xmlns="http://www.w3.org/2000/svg" width={size * 0.6} height={size * 0.6} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={svgClassName}>
                    <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"></path>
                    <path d="M20 3v4"></path>
                    <path d="M22 5h-4"></path>
                    <path d="M4 17v2"></path>
                    <path d="M5 18H3"></path>
                </svg>
            </div>

            {/* Brand Text */}
            {showText && (
                <span className="text-xl font-bold gradient-text">AI Shorts</span>
            )}
        </Link>
    );
}

export function AppLogoSvg({
    size = 40,
    showText = true,
    className = "",
    href = "/",
    svgClassName = "w-6 h-6 text-white",
}: AppLogoProps) {
    return (
        <div
            className={cn(
                "rounded-xl bg-gradient-to-br logo-icon-bg  from-primary  to-accent flex items-center justify-center",
            )}
            style={{ width: size, height: size }}
        >

            <svg xmlns="http://www.w3.org/2000/svg" width={size * 0.6} height={size * 0.6} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={svgClassName}>
                <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"></path>
                <path d="M20 3v4"></path>
                <path d="M22 5h-4"></path>
                <path d="M4 17v2"></path>
                <path d="M5 18H3"></path>
            </svg>
        </div>
    );
}
