"use client";

import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/context/AuthContext";
import ClientThemeProvider from "@/components/providers/ClientThemeProvider";

export default function ClientProviders({
    children,
}: {
    children: React.ReactNode;
}) {
    const [queryClient] = useState(() => new QueryClient());

    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                <ClientThemeProvider>
                    {children}
                </ClientThemeProvider>
            </AuthProvider>
        </QueryClientProvider>
    );
}
