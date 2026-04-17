import { getLatestDigest, formatDate, getAllArticles, fillEmptySections, getLatestStocksFromHistory, getHomepageArticles } from "@/lib/data";
import StockTicker from "@/components/StockTicker";
import HeroBanner from "@/components/HeroBanner";
import KeyPoints from "@/components/KeyPoints";
import ExecutiveSummary from "@/components/ExecutiveSummary";
import ArticleCard from "@/components/ArticleCard";
import PodcastPlayer from "@/components/PodcastPlayer";
import StockChart from "@/components/StockChart";
import Link from "next/link";
import fs from "fs";
import path from "path";

export const dynamic = "force-dynamic";

function getWeeklyMeta(): { date: string; daysAgo: number } | null {
  try {
    const metaPath = path.join(process.cwd(), "public", "data", "weekly_meta.json");
    if (!fs.existsSync(metaPath)) return null;
    const meta = JSON.parse(fs.readFileSync(metaPath, "utf-8"));
    if (!meta.date) return null;
    const published = new Date(meta.date + "T12:00:00");
    const daysAgo = Math.floor((Date.now() - published.getTime()) / 86400000);
    if (daysAgo > 7) return null;
    return { date: meta.date, daysAgo };
  } catch {
    return null;
  }
}

function formatWeekLabel(dateStr: string): string {
  try {
    const d = new Date(dateStr + "T12:00:00");
    const start = new Date(d);
    start.setDate(d.getDate() - 6);
    const opts: Intl.DateTimeFormatOptions = { month: "long", day: "numeric" };
    return `${start.toLocaleDateString("en-US", opts)} – ${d.toLocaleDateString("en-US", { ...opts, year: "numeric" })}`;
  } catch {
    return dateStr;
  }
}

export default function HomePage() {
  let data = getLatestDigest();
  const weeklyMeta = getWeeklyMeta();

  // Fill empty sections with historical articles
  data = fillEmptySections(data);

  // Use historical stock data if today's is empty
  if (!data.stocks || Object.keys(data.stocks).length === 0) {
    data.stocks = getLatestStocksFromHistory();
  }

  // Display sections in this specific order
  const sectionOrder = ["aortic", "surgical", "mitral", "tricuspid", "trials", "regulatory"];
  const allSections = sectionOrder
    .filter((key) => data.sections[key])
    .map((key) => [key, data.sections[key]] as [string, typeof data.sections[string]]);
  const totalArticles = getAllArticles(data).length;

  return (
    <>
      {/* Stock Ticker */}
      <StockTicker stocks={data.stocks} />

      {/* Hero Banner */}
      <HeroBanner date={formatDate(data.date)} articleCount={totalArticles} />

      {/* Weekly Digest Banner — shown when weekly is fresh (within 7 days) */}
      {weeklyMeta && (
        <div className="bg-[var(--color-wine)] text-white">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="nav-font text-xs font-semibold uppercase tracking-widest text-[var(--color-rose)]">
                {weeklyMeta.daysAgo === 0 ? "Just Published" : weeklyMeta.daysAgo === 1 ? "Yesterday" : `${weeklyMeta.daysAgo} days ago`}
              </span>
              <span className="text-white/30">|</span>
              <span className="nav-font text-sm font-medium text-white">
                The Valve Wire Weekly — {formatWeekLabel(weeklyMeta.date)}
              </span>
            </div>
            <Link
              href="/weekly"
              className="nav-font text-xs font-semibold text-[var(--color-rose)] hover:text-white transition-colors whitespace-nowrap"
            >
              Read the full weekly →
            </Link>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Executive Summary + Weekly/Podcast sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-2">
            <ExecutiveSummary summary={data.executive_summary} />
            <KeyPoints points={data.key_points} />
          </div>
          <div className="space-y-6">
            <Link
              href="/weekly"
              className="block bg-white rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-shadow p-5 text-center"
            >
              <p className="nav-font text-xs font-semibold uppercase tracking-wider text-[var(--color-rose)] mb-1">
                {weeklyMeta ? "This Week" : "Weekly Digest"}
              </p>
              <h3 className="nav-font text-base font-medium text-[var(--color-wine)] mb-1">
                The Valve Wire Weekly
              </h3>
              <p className="text-xs text-gray-400">
                {weeklyMeta
                  ? `Week ending ${weeklyMeta.date}`
                  : "Publishes every Saturday"}
              </p>
              <span className="nav-font inline-block mt-3 text-xs text-[var(--color-rose)] font-medium">
                Read the full weekly →
              </span>
            </Link>
            <PodcastPlayer episode={data.podcast.latest_episode} />
          </div>
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-10">
            {allSections.map(([key, section]) => {
              if (key === "financial") return null; // handled separately below

              const displayArticles = getHomepageArticles(section.articles);
              const hasMore = section.articles.length > displayArticles.length;

              return (
                <div key={key} id={key} className="scroll-mt-24">
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
                  {/* Section commentary from daily digest */}
                  {section.commentary && (
                    <div
                      className="text-sm leading-relaxed text-gray-700 mb-4 prose prose-sm max-w-none [&_a]:text-[var(--color-burgundy)] [&_a]:underline [&_a]:hover:opacity-80 [&_strong]:text-[var(--color-wine)] [&_p]:mb-2"
                      dangerouslySetInnerHTML={{ __html: section.commentary }}
                    />
                  )}
                  <div className="space-y-4">
                    {displayArticles.map((article) => (
                      <ArticleCard
                        key={article.id}
                        article={article}
                        sectionColor={section.color}
                      />
                    ))}
                  </div>
                  {hasMore && (
                    <Link
                      href={`/archive?topic=${key}`}
                      className="nav-font inline-block mt-4 text-sm text-[var(--color-rose)] hover:underline font-medium"
                    >
                      View all {section.articles.length} {section.label.split("(")[0].trim()} articles →
                    </Link>
                  )}
                </div>
              );
            })}

            {/* Financial Section — permanent stock tracker + articles */}
            <div id="financial" className="scroll-mt-24">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-1 h-6 rounded-full" style={{ backgroundColor: "#8B7B3B" }} />
                <h2 className="nav-font text-xl font-medium text-[var(--color-wine)]">
                  Financial Analysis
                </h2>
              </div>

              {/* Permanent stock tracker */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-5 mb-4">
                <h3 className="nav-font text-sm font-bold uppercase tracking-wider text-[var(--color-burgundy)] mb-4">
                  Valve Industry Performance
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {Object.entries(data.stocks).map(([ticker, stock]) => {
                    const formatCap = (cap: string | number | undefined) => {
                      if (!cap) return null;
                      const num = typeof cap === "string" ? parseFloat(cap) : cap;
                      if (num >= 1e12) return `$${(num / 1e12).toFixed(1)}T`;
                      if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
                      if (num >= 1e6) return `$${(num / 1e6).toFixed(0)}M`;
                      return `$${num}`;
                    };
                    return (
                      <div key={ticker} className="bg-gray-50 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-1">
                          <span className="nav-font text-sm font-bold text-[var(--color-wine)]">{ticker}</span>
                          <span className="nav-font text-lg font-semibold">${(stock.price ?? 0).toFixed(2)}</span>
                        </div>
                        <p className="text-xs text-gray-400 mb-3">{stock.company}</p>

                        {/* Daily + 6M performance */}
                        <div className="flex justify-between nav-font text-xs mb-3">
                          <span className={stock.change_pct >= 0 ? "text-green-600" : "text-red-600"}>
                            Daily: {(stock.change_pct ?? 0) >= 0 ? "+" : ""}{(stock.change_pct ?? 0).toFixed(2)}%
                          </span>
                          <span className={(stock.change_6m_pct ?? 0) >= 0 ? "text-green-600" : "text-red-600"}>
                            6M: {(stock.change_6m_pct ?? 0) >= 0 ? "+" : ""}{(stock.change_6m_pct ?? 0).toFixed(1)}%
                          </span>
                        </div>

                        {/* 6M range bar */}
                        {stock.high_6m && stock.low_6m && stock.high_6m > stock.low_6m && (
                          <div className="mb-3">
                            <div className="flex justify-between nav-font text-[10px] text-gray-400 mb-1">
                              <span>${(stock.low_6m ?? 0).toFixed(0)}</span>
                              <span className="text-gray-500">6M Range</span>
                              <span>${(stock.high_6m ?? 0).toFixed(0)}</span>
                            </div>
                            <div className="h-1.5 bg-gray-200 rounded-full relative">
                              <div
                                className="absolute h-full bg-[var(--color-rose)] rounded-full"
                                style={{
                                  left: "0%",
                                  width: `${((stock.price - stock.low_6m) / (stock.high_6m - stock.low_6m)) * 100}%`,
                                }}
                              />
                            </div>
                          </div>
                        )}

                        {/* Key metrics */}
                        <div className="grid grid-cols-2 gap-x-4 gap-y-1 nav-font text-[11px]">
                          {formatCap(stock.market_cap) && (
                            <>
                              <span className="text-gray-400">Mkt Cap</span>
                              <span className="text-right text-gray-600 font-medium">{formatCap(stock.market_cap)}</span>
                            </>
                          )}
                          {stock.pe_ratio && (
                            <>
                              <span className="text-gray-400">P/E</span>
                              <span className="text-right text-gray-600 font-medium">{(stock.pe_ratio ?? 0).toFixed(1)}</span>
                            </>
                          )}
                          {stock.target_price && (
                            <>
                              <span className="text-gray-400">Target</span>
                              <span className="text-right text-gray-600 font-medium">${(stock.target_price ?? 0).toFixed(0)}</span>
                            </>
                          )}
                          {stock.recommendation && (
                            <>
                              <span className="text-gray-400">Consensus</span>
                              <span className="text-right text-gray-600 font-medium capitalize">{stock.recommendation}</span>
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Financial commentary from daily digest */}
              {data.sections.financial?.commentary && (
                <div
                  className="text-sm leading-relaxed text-gray-700 mb-4 prose prose-sm max-w-none [&_a]:text-[var(--color-burgundy)] [&_a]:underline [&_a]:hover:opacity-80 [&_strong]:text-[var(--color-wine)] [&_p]:mb-2"
                  dangerouslySetInnerHTML={{ __html: data.sections.financial.commentary }}
                />
              )}

              {/* Financial articles */}
              {data.sections.financial?.articles?.length > 0 && (
                <>
                  <div className="space-y-4">
                    {data.sections.financial.articles.slice(0, 5).map((article) => (
                      <ArticleCard
                        key={article.id}
                        article={article}
                        sectionColor="#8B7B3B"
                      />
                    ))}
                  </div>
                  {data.sections.financial.articles.length > 5 && (
                    <Link
                      href="/archive?topic=financial"
                      className="nav-font inline-block mt-4 text-sm text-[var(--color-rose)] hover:underline font-medium"
                    >
                      View all {data.sections.financial.articles.length} financial articles →
                    </Link>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <aside className="space-y-6">
            {/* Stock Charts */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-5">
              <h3 className="nav-font text-sm font-bold uppercase tracking-wider text-[var(--color-burgundy)] mb-4">
                Valve Industry Stocks
              </h3>
              <div className="space-y-3">
                {Object.entries(data.stocks).map(([ticker, stock]) => (
                  <StockChart
                    key={ticker}
                    ticker={ticker}
                    company={stock.company}
                    price={stock.price}
                    change_pct={stock.change_pct}
                    change_6m_pct={stock.change_6m_pct}
                    price_history={stock.price_history}
                  />
                ))}
              </div>
            </div>

            {/* Quick Links */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-5">
              <h3 className="nav-font text-sm font-bold uppercase tracking-wider text-[var(--color-burgundy)] mb-3">
                Quick Links
              </h3>
              <ul className="space-y-2 nav-font text-sm">
                <li>
                  <Link href="/archive" className="text-[var(--color-rose)] hover:underline">
                    Browse Archive
                  </Link>
                </li>
                <li>
                  <Link href="/podcast" className="text-[var(--color-rose)] hover:underline">
                    All Podcast Episodes
                  </Link>
                </li>
                <li>
                  <a href="/podcast/feed.xml" className="text-[var(--color-rose)] hover:underline">
                    RSS Feed
                  </a>
                </li>
              </ul>
            </div>

            {/* Subscribe CTA */}
            <div id="subscribe" className="bg-[var(--color-cream)] rounded-lg p-5 text-center scroll-mt-24">
              <h3 className="nav-font font-bold text-[var(--color-wine)] mb-2">
                Stay Informed
              </h3>
              <p className="text-sm text-[var(--color-burgundy)] mb-3">
                Get The Valve Wire delivered to your inbox every morning.
              </p>
              <a
                href="mailto:nolan.beckett@pm.me?subject=Subscribe%20to%20The%20Valve%20Wire"
                className="nav-font inline-block bg-[var(--color-rose)] text-white px-6 py-2 rounded-lg text-sm font-semibold hover:bg-[var(--color-burgundy)] transition-colors"
              >
                Subscribe
              </a>
            </div>
          </aside>
        </div>
      </div>
    </>
  );
}
