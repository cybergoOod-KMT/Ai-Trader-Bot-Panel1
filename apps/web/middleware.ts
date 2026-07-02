import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedPaths = [
  "/dashboard",
  "/settings",
  "/logs",
  "/notifications",
  "/force-change-password",
  "/manual-trading",
  "/ai-signal",
  "/ai-bot",
  "/strategy-bots",
  "/markets",
  "/orders",
  "/positions",
  "/script-trading",
  "/backtests",
  "/reports",
  "/audit-logs",
  "/learning-memory",
];

export function middleware(request: NextRequest) {
  const hasSession = Boolean(request.cookies.get("tabdeal_panel_session")?.value);
  const { pathname } = request.nextUrl;
  const isProtected = protectedPaths.some((path) => pathname.startsWith(path));

  if (isProtected && !hasSession) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (pathname === "/" && hasSession) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/",
    "/login",
    "/dashboard/:path*",
    "/settings/:path*",
    "/logs/:path*",
    "/notifications/:path*",
    "/force-change-password",
    "/manual-trading/:path*",
    "/ai-signal/:path*",
    "/ai-bot/:path*",
    "/strategy-bots/:path*",
    "/markets/:path*",
    "/orders/:path*",
    "/positions/:path*",
  ],
};
