import type { Metadata } from "next";
import localFont from "next/font/local";

import "@/styles/globals.css";
import "@/styles/theme-home.css";
import "@/styles/theme-dashboard.css";

import { headers } from "next/headers";
import ClientProviders from "@/components/providers/ClientProviders";


/* ✅ Use LOCAL Geist Variable Fonts */
const geistSans = localFont({
  src: "../../public/fonts/Geist/webfonts/Geist[wght].woff2",
  variable: "--font-geist-sans",
  weight: "100 900",
  display: "swap",
});

const geistMono = localFont({
  src: "../../public/fonts/GeistMono/webfonts/GeistMono[wght].woff2",
  variable: "--font-geist-mono",
  weight: "100 900",
  display: "swap",
});

const allowIndexing = process.env.NEXT_PUBLIC_INDEX_FOLLOW_ENABLED === "true";

async function getBaseUrl() {
  const h = await headers();
  const host = h.get("host") || "localhost:3000";
  const protocol = host.includes("localhost") ? "http" : "https";
  return `${protocol}://${host}`;
}

export async function generateMetadata(): Promise<Metadata> {
  const baseUrl = await getBaseUrl();

  return {
    title: {
      default: "AI Shorts – AI YouTube Automation",
      template: "%s | AI Shorts",
    },
    description:
      "Create AI-generated YouTube Shorts automatically using our advanced video automation system.",
    metadataBase: new URL(baseUrl),
    alternates: { canonical: baseUrl },
    robots: {
      index: allowIndexing,
      follow: allowIndexing,
      googleBot: {
        index: allowIndexing,
        follow: allowIndexing,
      },
    },
  };
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ClientProviders>
          {children}
        </ClientProviders>
      </body>
    </html>
  );
}
