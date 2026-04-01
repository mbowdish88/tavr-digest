import { getLatestDigest, formatDate, getAllArticles, fillEmptySections, getLatestStocksFromHistory, getHomepageArticles } from "@/lib/data";
import StockTicker from "@/components/StockTicker";
import HeroBanner from "@/components/HeroBanner";
import KeyPoints from "@/components/KeyPoints";
import ExecutiveSummary from "@/components/ExecutiveSummary";
import ArticleCard from "@/components/ArticleCard";
import PodcastPlayer from "@/components/PodcastPlayer";
import StockChart from "@/components/StockChart";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default function HomePage() {
  let data = getLatestDigest();

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
                Latest
              </p>
              <h3 className="nav-font text-base font-medium text-[var(--color-wine)] mb-1">
                Weekly Digest
              </h3>
              <p className="text-xs text-gray-400">
                {data.weekly_digests?.[0]
                  ? `Week ending ${data.weekly_digests[0].date}`
                  : "Latest weekly summary"}
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
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {Object.entries(data.stocks).map(([ticker, stock]) => (
                    <div key={ticker} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-1">
                        <span className="nav-font text-sm font-bold text-[var(--color-wine)]">{ticker}</span>
                        <span className="nav-font text-sm font-semibold">${stock.price.toFixed(2)}</span>
                      </div>
                      <p className="text-xs text-gray-400 mb-2">{stock.company}</p>
                      <div className="flex justify-between nav-font text-xs">
                        <span className={stock.change_pct >= 0 ? "text-green-600" : "text-red-600"}>
                          Daily: {stock.change_pct >= 0 ? "+" : ""}{stock.change_pct.toFixed(2)}%
                        </span>
                        <span className={stock.change_6m_pct >= 0 ? "text-green-600" : "text-red-600"}>
                          6M: {stock.change_6m_pct >= 0 ? "+" : ""}{stock.change_6m_pct.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

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
