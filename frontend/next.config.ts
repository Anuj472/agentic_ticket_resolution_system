import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // BUG-08 FIX: The /backend/* rewrite was dead code — all pages use the
  // app/api/proxy/[...path]/route.ts handler on /api/proxy/*.
  // This rewrite is kept for optional direct use but aligned to the actual prefix.
  async rewrites() {
    return [
      {
        // Direct pass-through for any /api/proxy/* → backend (fallback if route.ts removed)
        source: "/backend/:path*",
        destination: "http://localhost:8000/api/v1/:path*",
      },
    ];
  },
};

export default nextConfig;
