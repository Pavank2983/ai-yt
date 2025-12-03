import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// SIMPLE JWT DECODER (works on edge runtime)
function decodeToken(token: string) {
    try {
        const payload = token.split(".")[1];
        return JSON.parse(Buffer.from(payload, "base64url").toString());
    } catch {
        return null;
    }
}

// PUBLIC PAGES
const PUBLIC_AUTH_PAGES = ["/login", "/register"];
const PROTECTED_PREFIX = "/dashboard";

// ROLE PERMISSION MAP
const ROLE_ACCESS: Record<string, string[]> = {
    viewer: [
        "/dashboard",
        "/dashboard/channels",
        "/dashboard/support",
        "/dashboard/profile",
    ],

    editor: [
        "/dashboard",
        "/dashboard/scripts",
        "/dashboard/voices",
        "/dashboard/videos",
        "/dashboard/jobs",
        "/dashboard/uploaded-videos",
        "/dashboard/metadata",
        "/dashboard/channels",
        "/dashboard/support",
        "/dashboard/profile",
    ],

    admin: [
        "/dashboard",
        "/dashboard/scripts",
        "/dashboard/voices",
        "/dashboard/videos",
        "/dashboard/jobs",
        "/dashboard/uploaded-videos",
        "/dashboard/metadata",
        "/dashboard/channels",
        "/dashboard/support",
        "/dashboard/profile",
        "/dashboard/admin",
        "/dashboard/admin/",       // admin/anything
    ],
};

// helper to check access
function isAllowed(role: string, path: string) {
    const allowed = ROLE_ACCESS[role] || [];
    return allowed.some((rule) => path.startsWith(rule));
}

export function middleware(req: NextRequest) {
    const { pathname } = req.nextUrl;

    const token = req.cookies.get("access_token")?.value || null;

    // 1. NO TOKEN → guest
    if (!token) {
        if (pathname.startsWith(PROTECTED_PREFIX)) {
            return NextResponse.redirect(new URL("/login", req.url));
        }
        return NextResponse.next();
    }

    // 2. DECODE TOKEN SAFELY
    const decoded = decodeToken(token);
    if (!decoded) {
        return NextResponse.redirect(new URL("/login", req.url));
    }

    // 3. CHECK EXPIRATION
    const now = Math.floor(Date.now() / 1000);
    if (decoded.exp && decoded.exp < now) {
        // expired → force logout
        const res = NextResponse.redirect(new URL("/login", req.url));
        res.cookies.delete("access_token");
        return res;
    }

    const role = decoded.role || "guest";

    // 4. Logged user must NOT see login/register
    if (PUBLIC_AUTH_PAGES.includes(pathname)) {
        return NextResponse.redirect(new URL("/dashboard", req.url));
    }

    // 5. Protected routes → role check
    if (pathname.startsWith(PROTECTED_PREFIX)) {
        if (!isAllowed(role, pathname)) {
            return NextResponse.redirect(new URL("/403", req.url));
        }
    }

    return NextResponse.next();
}

// MATCHER
export const config = {
    matcher: [
        "/dashboard/:path*",
        "/login",
        "/register",
    ],
};
