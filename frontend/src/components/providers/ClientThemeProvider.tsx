"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";

export default function ClientThemeProvider({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();

    useEffect(() => {
        const body = document.body;

        if (pathname.startsWith("/dashboard")) {
            body.classList.add("theme-dashboard");
            body.classList.remove("theme-home");
        } else {
            body.classList.add("theme-home");
            body.classList.remove("theme-dashboard");
        }
    }, [pathname]);

    return <>{children}</>;
}
