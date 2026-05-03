import { NextRequest, NextResponse } from "next/server";

const BACKEND = "http://127.0.0.1:80/api/v1";

// Hop-by-hop headers — never forward to upstream
const SKIP_HEADERS = new Set([
  "host", "connection", "transfer-encoding", "expect",
  "keep-alive", "proxy-authenticate", "proxy-authorization",
  "te", "trailers", "upgrade",
]);

async function handler(req: NextRequest): Promise<NextResponse> {
  // Strip /api/proxy prefix, keep exact path
  const path = req.nextUrl.pathname.replace("/api/proxy", "");
  const url  = `${BACKEND}${path}${req.nextUrl.search}`;

  // Build forwarded headers (strip hop-by-hop)
  const headers: Record<string, string> = {};
  req.headers.forEach((v, k) => {
    if (!SKIP_HEADERS.has(k.toLowerCase())) headers[k] = v;
  });

  // Body for POST/PUT/PATCH
  const hasBody = !["GET", "HEAD"].includes(req.method.toUpperCase());
  const body    = hasBody ? await req.text() : undefined;
  if (hasBody && body) {
    headers["content-length"] = Buffer.byteLength(body, "utf-8").toString();
  }

  let res: Response;
  try {
    // Step 1: fetch with redirect:manual so we can re-attach headers on redirect
    res = await fetch(url, { method: req.method, headers, body, redirect: "manual" });

    // Step 2: follow 307/308 manually — preserving Authorization and all other headers.
    // FastAPI (redirect_slashes=True) sends 307 when the path needs a slash correction.
    // fetch(redirect:"follow") strips Authorization on cross-host redirects, so we do it ourselves.
    if (res.status === 307 || res.status === 308) {
      const location   = res.headers.get("location") ?? "";
      const redirectTo = location.startsWith("http")
        ? location
        : `http://127.0.0.1:80${location}`;
      res = await fetch(redirectTo, { method: req.method, headers, body });
    }
  } catch (err: any) {
    return new NextResponse(
      JSON.stringify({ detail: `Proxy connection error: ${err.message}` }),
      { status: 502, headers: { "Content-Type": "application/json" } }
    );
  }

  const text        = await res.text();
  const contentType = res.headers.get("Content-Type") ?? "application/json";
  return new NextResponse(text, {
    status:  res.status,
    headers: { "Content-Type": contentType },
  });
}

export const GET    = handler;
export const POST   = handler;
export const PUT    = handler;
export const PATCH  = handler;
export const DELETE = handler;