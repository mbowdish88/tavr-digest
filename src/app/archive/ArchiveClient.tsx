"use client";

import { useState } from "react";
import type { DigestData, Article } from "@/lib/data";
import ArticleCard from "@/components/ArticleCard";
import Link from "next/link";

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

export default function ArchiveClient({ data, allArticles, dates }: ArchiveClientProps) {
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  // Use historical articles if available, fall back to today's
  const articles = allArticles.length > 0
    ? allArticles
    : Object.entries(data.sections).flatMap(([key, section]) =>
        section.articles.map((a) => ({ ...a, digestDate: data.date, sectionKey: key, sectionColor: section.color }))
      );

  // Filter articles
  const filtered = articles.filter((article) => {
    if (activeFilter && article.sectionKey !== activeFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        article.title.toLowerCase().includes(q) ||
        article.abstract.toLowerCase().includes(q) ||
        (article.authors || "").toLowerCase().includes(q) ||
        article.source.toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Section counts across all articles
  const sectionCounts: Record<string, number> = {};
  for (const a of articles) {
    sectionCounts[a.sectionKey] = (sectionCounts[a.sectionKey] || 0) + 1;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <div className="mb-8">
        <p className="nav-font text-xs font-semibold uppercase tracking-widest text-[var(--color-rose)] mb-1">
          Archive
        </p>
        <h1 className="text-3xl font-bold text-[var(--color-wine)] mb-2">
          All Articles
        </h1>
        <p className="nav-font text-sm text-gray-500 mb-4">
          {articles.length} articles across {dates.length} {dates.length === 1 ? "digest" : "digests"}
        </p>

        {/* Digest date links */}
        {dates.length > 1 && (
          <div className="flex flex-wrap gap-2 mb-4 nav-font text-xs">
            {dates.map((d) => (
              <span key={d} className="px-2 py-1 rounded bg-gray-100 text-gray-600">
                {d}
              </span>
            ))}
          </div>
        )}

        {/* Search */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search articles by title, author, source..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full max-w-lg px-4 py-2 rounded-lg border border-gray-200 nav-font text-sm focus:outline-none focus:border-[var(--color-rose)] focus:ring-1 focus:ring-[var(--color-rose)]"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2 nav-font text-sm">
          <button
            onClick={() => setActiveFilter(null)}
            className={`px-3 py-1.5 rounded-full border transition-colors font-semibold ${
              activeFilter === null
                ? "bg-[var(--color-wine)] text-white border-[var(--color-wine)]"
                : "border-gray-200 text-gray-600 hover:border-[var(--color-rose)]"
            }`}
          >
            All ({articles.length})
          </button>
          {Object.entries(data.sections).map(([key, section]) => (
            <button
              key={key}
              onClick={() => setActiveFilter(activeFilter === key ? null : key)}
              className={`px-3 py-1.5 rounded-full border transition-colors font-semibold ${
                activeFilter === key
                  ? "text-white border-transparent shadow-sm"
                  : "border-gray-200 text-gray-600 hover:border-[var(--color-rose)]"
              }`}
              style={
                activeFilter === key
                  ? { backgroundColor: section.color }
                  : { borderColor: section.color + "40" }
              }
            >
              <span
                className="inline-block w-2 h-2 rounded-full mr-1.5"
                style={{ backgroundColor: activeFilter === key ? "white" : section.color }}
              />
              {section.label.split("(")[0].trim()}
              <span className="ml-1 text-xs opacity-70">({sectionCounts[key] || 0})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Results count */}
      {(activeFilter || searchQuery) && (
        <p className="nav-font text-sm text-gray-500 mb-4">
          Showing {filtered.length} of {articles.length} articles
          {activeFilter && ` in ${data.sections[activeFilter]?.label}`}
          {searchQuery && ` matching "${searchQuery}"`}
        </p>
      )}

      {/* Article Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((article, i) => (
          <ArticleCard key={`${article.id}-${article.digestDate}-${i}`} article={article} sectionColor={article.sectionColor} />
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="text-center text-gray-400 py-12">
          No articles found.{" "}
          {(activeFilter || searchQuery) && (
            <button
              onClick={() => { setActiveFilter(null); setSearchQuery(""); }}
              className="text-[var(--color-rose)] hover:underline"
            >
              Clear filters
            </button>
          )}
        </p>
      )}
    </div>
  );
}
