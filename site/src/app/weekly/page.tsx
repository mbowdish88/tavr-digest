import type { Metadata } from "next";
import fs from "fs";
import path from "path";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Weekly Digest | The Valve Wire",
  description: "The Valve Wire Weekly — comprehensive weekly summary of structural heart disease developments.",
};

export const dynamic = "force-dynamic";

function getWeeklyData(): { html: string | null; date: string | null; archives: string[] } {
  const dataDir = path.join(process.cwd(), "public", "data");

  // Load the latest weekly HTML
  let html: string | null = null;
  let date: string | null = null;

  const latestPath = path.join(dataDir, "weekly_latest.html");
  if (fs.existsSync(latestPath)) {
    html = fs.readFileSync(latestPath, "utf-8");
  }

  // Load metadata for date
  const metaPath = path.join(dataDir, "weekly_meta.json");
  if (fs.existsSync(metaPath)) {
    try {
      const meta = JSON.parse(fs.readFileSync(metaPath, "utf-8"));
      date = meta.date || null;
    } catch {}
  }

  // Find dated archive files
  const archives: string[] = [];
  try {
    const files = fs.readdirSync(dataDir);
    files
      .filter((f) => f.match(/^weekly_\d{4}-\d{2}-\d{2}\.html$/))
      .sort()
      .reverse()
      .slice(0, 8) // keep last 8 weeks
      .forEach((f) => {
        const d = f.replace("weekly_", "").replace(".html", "");
        if (d !== date) archives.push(d);
      });
  } catch {}

  return { html, date, archives };
}

function formatWeekDate(dateStr: string): string {
  try {
    const d = new Date(dateStr + "T12:00:00");
    const start = new Date(d);
    start.setDate(d.getDate() - 6);
    const opts: Intl.DateTimeFormatOptions = { month: "long", day: "numeric" };
    return `Week of ${start.toLocaleDateString("en-US", opts)} – ${d.toLocaleDateString("en-US", { ...opts, year: "numeric" })}`;
  } catch {
    return dateStr;
  }
}

export default function WeeklyPage() {
  const { html, date, archives } = getWeeklyData();

  if (!html) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <p className="nav-font text-xs font-semibold uppercase tracking-widest text-[var(--color-rose)] mb-3">
          Weekly Digest
        </p>
        <h1 className="text-3xl font-bold text-[var(--color-wine)] mb-4">
          The Valve Wire Weekly
        </h1>
        <p className="text-gray-500 mb-6">
          The weekly digest publishes every Saturday at midnight Eastern. Check back then.
        </p>
        <Link href="/" className="nav-font text-sm text-[var(--color-rose)] hover:underline">
          ← Back to today&apos;s digest
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8 pb-6 border-b border-gray-200">
        <p className="nav-font text-xs font-semibold uppercase tracking-widest text-[var(--color-rose)] mb-2">
          Weekly Digest
        </p>
        <h1 className="text-3xl font-bold text-[var(--color-wine)] mb-1">
          The Valve Wire Weekly
        </h1>
        {date && (
          <p className="text-gray-500 text-sm nav-font">{formatWeekDate(date)}</p>
        )}
        <div className="flex gap-4 mt-4">
          <Link href="/" className="nav-font text-xs text-[var(--color-rose)] hover:underline">
            ← Daily digest
          </Link>
          <Link href="/archive" className="nav-font text-xs text-[var(--color-rose)] hover:underline">
            Archive →
          </Link>
        </div>
      </div>

      {/* Full newsletter HTML */}
      <div
        className="weekly-content prose max-w-none"
        dangerouslySetInnerHTML={{ __html: html }}
      />

      {/* Archive */}
      {archives.length > 0 && (
        <div className="mt-12 pt-8 border-t border-gray-200">
          <h2 className="nav-font text-sm font-semibold uppercase tracking-widest text-[var(--color-wine)] mb-4">
            Previous Issues
          </h2>
          <ul className="space-y-2">
            {archives.map((d) => (
              <li key={d}>
                <Link
                  href={`/weekly/${d}`}
                  className="nav-font text-sm text-[var(--color-rose)] hover:underline"
                >
                  {formatWeekDate(d)}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
