import { NextRequest } from "next/server";

export const runtime = "edge";

const REPO = "mbowdish88/tavr-digest";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ date: string }> },
) {
  const { date } = await params;

  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return new Response("Invalid date", { status: 400 });
  }

  const upstream = `https://github.com/${REPO}/releases/download/podcast-${date}/${date}_valve_wire_weekly.mp3`;

  const upstreamHeaders: HeadersInit = {};
  const range = req.headers.get("range");
  if (range) upstreamHeaders["Range"] = range;

  const upstreamRes = await fetch(upstream, {
    headers: upstreamHeaders,
    redirect: "follow",
  });

  if (!upstreamRes.ok && upstreamRes.status !== 206) {
    return new Response(`Upstream returned ${upstreamRes.status}`, {
      status: upstreamRes.status,
    });
  }

  const headers = new Headers();
  headers.set("Content-Type", "audio/mpeg");
  headers.set("Content-Disposition", `inline; filename="${date}.mp3"`);
  headers.set("Accept-Ranges", "bytes");
  // s-maxage=0 prevents Vercel CDN from caching the full response and
  // serving it back for Range requests as 200 — which breaks iOS Safari,
  // since Safari only plays audio when the server responds 206 to its
  // initial Range probe.
  headers.set("Cache-Control", "public, max-age=3600, s-maxage=0");
  headers.set("Vary", "Range");

  const passthrough = ["content-length", "content-range", "etag", "last-modified"];
  for (const h of passthrough) {
    const v = upstreamRes.headers.get(h);
    if (v) headers.set(h, v);
  }

  return new Response(upstreamRes.body, {
    status: upstreamRes.status,
    headers,
  });
}
