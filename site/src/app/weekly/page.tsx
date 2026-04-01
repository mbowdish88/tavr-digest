import type { Metadata } from "next";
import { getLatestDigest, getAllDigestDates, getDigestByDate } from "@/lib/data";
import ArticleCard from "@/components/ArticleCard";
import ExecutiveSummary from "@/components/ExecutiveSummary";
import KeyPoints from "@/components/KeyPoints";
import fs from "fs";
import path from "path";

export const metadata: Metadata = {
  title: "Weekly Digest",
  description: "The Valve Wire Weekly — comprehensive weekly summary of structural heart disease developments.",
};

export const dynamic = "force-dynamic";

function getLatestWeeklyDigest() {
  const digestsDir = path.join(process.cwd(), "public", "data", "digests");
  try {
    const files = fs.readdirSync(digestsDir);
    const weeklyFiles = files
      .filter((f: string) => f.startsWith("weekly-") && f.endsWith(".json"))
      .sort()
      .reverse();

    if (weeklyFiles.length > 0) {
      const raw = fs.readFileSync(path.join(digestsDir, weeklyFiles[0]), "utf-8");
      return JSON.parse(raw);
    }
  } catch {}
  return null;
}

export default function WeeklyPage() {
  const weekly = getLatestWeeklyDigest();

  if (!weekly) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <h1 className="text-2xl font-bold text-[var(--color-wine)] mb-4">Weekly Digest</h1>
        <p className="text-gray-500">No weekly digest available yet.</p>
      </div>
    );
  }

  const allSections = Object.entries(weekly.sections || {});

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <p className="nav-font text-xs font-semibold uppercase tracking-widest text-[var(--color-rose)] mb-1">
          Weekly Digest
        </p>
        <h1 className="text-3xl font-bold text-[var(--color-wine)]">
          Week ending {weekly.date}
        </h1>
      </div>

      {weekly.executive_summary && (
        <ExecutiveSummary summary={weekly.executive_summary} />
      )}

      {weekly.key_points?.length > 0 && (
        <KeyPoints points={weekly.key_points} />
      )}

      <div className="space-y-10">
        {allSections.map(([key, section]: [string, any]) => {
          if (!section.articles?.length) return null;
          return (
            <div key={key}>
              <div className="flex items-center gap-3 mb-4">
                <div
                  className="w-1 h-6 rounded-full"
                  style={{ backgroundColor: section.color }}
                />
                <h2 className="nav-font text-xl font-medium text-[var(--color-wine)]">
                  {section.label}
                </h2>
                <span className="nav-font text-xs text-gray-400">
                  {section.articles.length} {section.articles.length === 1 ? "article" : "articles"}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {section.articles.map((article: any) => (
                  <ArticleCard
                    key={article.id}
                    article={article}
                    sectionColor={section.color}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
