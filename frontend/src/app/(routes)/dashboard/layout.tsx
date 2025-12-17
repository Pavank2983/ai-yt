"use client";

import "@/styles/theme-dashboard.css";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, loading } = useAuth();

  const [isSidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!loading && !user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background flex font-sans">
      <Sidebar
        isOpen={isSidebarOpen}
        toggle={() => setSidebarOpen(!isSidebarOpen)}
      />

      <div
        className={cn(
          "flex min-h-screen flex-col transition-all duration-300 ease-in-out w-full",
          isSidebarOpen ? "md:ml-60" : "md:ml-[72px]"
        )}
      >
        <Topbar onMenuClick={() => setSidebarOpen(!isSidebarOpen)} />

        <main className="flex-1 overflow-x-hidden p-4 md:p-8 pt-6 max-w-7xl mx-auto w-full">
          <div className="animate-in fade-in-0 slide-in-from-bottom-3 duration-500 ease-out">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
