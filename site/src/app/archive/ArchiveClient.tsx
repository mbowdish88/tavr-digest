"use client";

import { useState, useEffect } from "react";
import type { DigestData, Article } from "@/lib/data";
import ArticleCard from "@/components/ArticleCard";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";

interface ArchiveArticle extends Article {
  digestDate: string;
  sectionKey: string;
  sectionColor: string;
}

interface ArchiveClientProps {
  data: DigestData;
  allArticles: ArchiveArticle[];
  dates: string[];
}

const TOPICS = [
  { key: "aortic",     label: "Aortic" },
  { key: "mitral",     label: "Mitral" },
  { key: "tricuspid",  label: "Tricuspid" },
  { key: "surgical",   label: "Surgical" },
  { key: "trials",     label: "Trials" },
  { key: "regulatory", label: "Regulatory" },
  { key: "financial",  label: "Financial" },
];

// Journal hierarchy for topic view sorting (mirrors data.ts, inlined for client component)
const JOURNAL_TIER_MAP: [string, number][] = [
  ["new england journal", 1], ["nejm", 1], ["n engl j med", 1],
  ["jama", 2],
  ["jacc: cardiovascular interventions", 6], ["jacc cardiovasc interv", 6], ["jacc.ci", 6], ["jacc:ci", 6],
  ["jacc", 3], ["j am coll cardiol", 3],
  ["lancet", 4],
  ["european heart journal", 5], ["eur heart j", 5], ["ehj", 5],
  ["annals of thoracic surgery", 7], ["ann thorac surg", 7],
  ["journal of thoracic and cardiovascular surgery", 8], ["j thorac cardiovasc surg", 8], ["jtcvs", 8],
  ["european journal of cardio-thoracic surgery", 9], ["eur j cardiothorac surg", 9], ["ejcts", 9],
];

function getJournalTier(source: string): number {
  if (!source) return 99;
  const lower = source.toLowerCase();
  for (const [journal, tier] of JOURNAL_TIER_MAP) {
    if (lower.includes(journal)) return tier;
  }
  return 99;
}

function sortByJournalHierarchy<T extends { source: string; date: string }>(articles: T[]): T[] {
  return [...articles].sort((a, b) => {
    const tierA = getJournalTier(a.source);
    const tierB = getJournalTier(b.source);
    if (tierA !== tierB) return tierA - tierB;
    return (b.date || "").localeCompare(a.date || "");
  });
}

const TOPIC_COLORS: Record<string, string> = {
  aortic:     "#2C5282",
  mitral:     "#3182CE",
  tricuspid:  "#6B46C1",
  surgical:   "#2F855A",
  trials:     "#744210",
  regulatory: "#276749",
  financial:  "#8B7B3B",
};

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr + "T12:00:00");
    return d.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function formatShortDate(dateStr: string): string {
  try {
    const d = new Date(dateStr + "T12:00:00");
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export default function ArchiveClient({ data, allArticles, dates }: ArchiveClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Active topic from URL query param (e.g. ?topic=aortic) or state
  const initialTopic = searchParams.get("topic") || null;
  const [activeTopic, setActiveTopic] = useState<string | null>(initialTopic);

  // Sync URL when topic changes
  function handleTopicChange(topic: string | null) {
    setActiveTopic(topic);
    const url = topic ? `/archive?topic=${topic}` : "/archive";
    router.replace(url, { scroll: false });
  }

  // When in topic mode, show all articles for that topic across all dates, sorted by journal hierarchy
  const topicArticles: ArchiveArticle[] = activeTopic
    ? sortByJournalHierarchy(allArticles.filter((a) => a.sectionKey === activeTopic))
    : [];

  // Article count per topic across all dates
  const topicCounts: Record<string, number> = {};
  for (const a of allArticles) {
    topicCounts[a.sectionKey] = (topicCounts[a.sectionKey] || 0) + 1;
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      {/* Page header */}
      <div className="mb-8 pb-6 border-b border-gray-200">
        <p className="nav-font text-xs font-semibold uppercase tracking-widest text-[var(--color-rose)] mb-1">
          Archive
        </p>
        <h1 className="text-3xl font-bold text-[var(--color-wine)] mb-1">
          The Valve Wire Archive
        </h1>
        <p className="nav-font text-sm text-gray-500">
          {dates.length} {dates.length === 1 ? "digest" : "digests"} &middot; {allArticles.length} articles
        </p>
        <div className="flex gap-4 mt-3">
          <Link href="/" className="nav-font text-xs text-[var(--color-rose)] hover:underline">
            ← Today&apos;s digest
          </Link>
          <Link href="/weekly" className="nav-font text-xs text-[var(--color-rose)] hover:underline">
            Weekly digest →
          </Link>
        </div>
      </div>

      {/* Topic filter buttons */}
      <div className="mb-8">
        <p className="nav-font text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">
          Browse by topic
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleTopicChange(null)}
            className={`nav-font px-4 py-2 rounded-full text-sm font-semibold border transition-colors ${
              activeTopic === null
                ? "bg-[var(--color-wine)] text-white border-[var(--color-wine)]"
                : "border-gray-200 text-gray-600 hover:border-[var(--color-wine)] hover:text-[var(--color-wine)]"
            }`}
          >
            All Digests
          </button>
          {TOPICS.map(({ key, label }) => {
            const color = TOPIC_COLORS[key] || "#2C5282";
            const count = topicCounts[key] || 0;
            const isActive = activeTopic === key;
            return (
              <button
                key={key}
                onClick={() => handleTopicChange(isActive ? null : key)}
                className={`nav-font px-4 py-2 rounded-full text-sm font-semibold border transition-colors ${
                  isActive
                    ? "text-white border-transparent"
                    : "border-gray-200 text-gray-600 hover:border-opacity-60"
                }`}
                style={
                  isActive
                    ? { backgroundColor: color, borderColor: color }
                    : { borderColor: color + "50", color: color }
                }
              >
                {label}
                <span className="ml-1.5 text-xs opacity-70">({count})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* TOPIC MODE — article list */}
      {activeTopic && (
        <div>
          <div className="flex items-center gap-3 mb-6">
            <div
              className="w-1 h-6 rounded-full"
              style={{ backgroundColor: TOPIC_COLORS[activeTopic] || "#2C5282" }}
            />
            <h2 className="nav-font text-xl font-semibold text-[var(--color-wine)]">
              {TOPICS.find((t) => t.key === activeTopic)?.label} — All Articles
            </h2>
            <span className="nav-font text-sm text-gray-400">
              {topicArticles.length} {topicArticles.length === 1 ? "article" : "articles"}
            </span>
          </div>

          {topicArticles.length === 0 ? (
            <p className="text-center text-gray-400 py-12 nav-font text-sm">
              No articles found for this topic.
            </p>
          ) : (
            <div className="space-y-4">
              {topicArticles.map((article, i) => (
                <ArticleCard
                  key={`${article.id}-${article.digestDate}-${i}`}
                  article={article}
                  sectionColor={TOPIC_COLORS[activeTopic] || article.sectionColor}
                  fullAbstract
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* DATE LIST MODE — chronological list of digest days */}
      {!activeTopic && (
        <div>
          <p className="nav-font text-xs font-semibold uppercase tracking-widest text-gray-400 mb-4">
            Daily Digests
          </p>
          {dates.length === 0 ? (
            <p className="text-center text-gray-400 py-12 nav-font text-sm">
              No digests available.
            </p>
          ) : (
            <div className="space-y-2">
              {dates.map((dateStr) => (
                <Link
                  key={dateStr}
                  href={`/archive/${dateStr}`}
                  className="group flex items-center justify-between px-5 py-4 bg-white rounded-lg border border-gray-100 shadow-sm hover:shadow-md hover:border-[var(--color-rose)] transition-all"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-1.5 h-8 rounded-full bg-[var(--color-rose)] opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div>
                      <p className="nav-font text-sm font-semibold text-[var(--color-wine)] group-hover:text-[var(--color-rose)] transition-colors">
                        {formatDate(dateStr)}
                      </p>
                      <p className="nav-font text-xs text-gray-400 mt-0.5">
                        Daily digest &middot; Full newsletter
                      </p>
                    </div>
                  </div>
                  <span className="nav-font text-xs text-gray-400 group-hover:text-[var(--color-rose)] transition-colors">
                    Read →
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
