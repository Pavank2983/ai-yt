"use client";

import { usePathname } from "next/navigation";

export default function useIsDashboard() {
    const pathname = usePathname() || "/";
    // treat anything starting with /dashboard as dashboard
    return pathname.startsWith("/dashboard");
}
