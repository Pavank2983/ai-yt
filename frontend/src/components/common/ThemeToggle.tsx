"use client";

import { useEffect, useState } from "react";

export default function ThemeToggle({ className = "" }: { className?: string }) {
    const [theme, setTheme] = useState<"light" | "dark">("light");

    useEffect(() => {
        const stored = localStorage.getItem("theme");
        const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
        const initial = (stored as "light" | "dark") || (prefersDark ? "dark" : "light");
        setTheme(initial);
        document.documentElement.classList.toggle("dark", initial === "dark");
    }, []);

    const toggle = () => {
        const next = theme === "dark" ? "light" : "dark";
        setTheme(next);
        localStorage.setItem("theme", next);
        document.documentElement.classList.toggle("dark", next === "dark");
    };

    return (
        <button
            aria-label="Toggle theme"
            onClick={toggle}
            className={`inline-flex items-center justify-center rounded-md p-2 text-sm ring-offset-white focus:outline-none focus:ring-2 ${className}`}
            title="Toggle theme"
        >
            {theme === "dark" ? "🌙" : "☀️"}
        </button>
    );
}
