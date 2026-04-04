import fs from "fs";
import path from "path";

/**
 * Journal hierarchy for homepage display.
 * Tier 1-2 journals ALWAYS make the front page, even if it pushes past 5 articles.
 * Lower tiers fill remaining slots up to 5.
 */
const JOURNAL_TIERS: Record<string, number> = {
  // Tier 1 — always front page
  "New England Journal of Medicine": 1,
  "NEJM": 1,
  "N Engl J Med": 1,
  "JAMA": 2,
  "Journal of the American Medical Association": 2,
  "JACC": 3,
  "Journal of the American College of Cardiology": 3,
  "J Am Coll Cardiol": 3,
  "Lancet": 4,
  "The Lancet": 4,
  "European Heart Journal": 5,
  "Eur Heart J": 5,
  "EHJ": 5,
  // Tier 2 — always front page
  "JACC: Cardiovascular Interventions": 6,
  "JACC Cardiovasc Interv": 6,
  // Tier 3 — surgical journals
  "Annals of Thoracic Surgery": 7,
  "Ann Thorac Surg": 7,
  "Journal of Thoracic and Cardiovascular Surgery": 8,
  "J Thorac Cardiovasc Surg": 8,
  "JTCVS": 8,
  "European Journal of Cardio-Thoracic Surgery": 9,
  "Eur J Cardiothorac Surg": 9,
  "EJCTS": 9,
};
const ALWAYS_FRONT_PAGE_TIER = 6; // Tier 1-2 (values 1-6) always on front page
const DEFAULT_TIER = 99;

function getJournalTier(source: string): number {
  if (!source) return DEFAULT_TIER;
  // Direct match
  if (JOURNAL_TIERS[source] !== undefined) return JOURNAL_TIERS[source];
  // Partial match
  const lower = source.toLowerCase();
  for (const [journal, tier] of Object.entries(JOURNAL_TIERS)) {
    if (lower.includes(journal.toLowerCase()) || journal.toLowerCase().includes(lower)) {
      return tier;
    }
  }
  return DEFAULT_TIER;
}

export function sortByJournalHierarchy(articles: Article[]): Article[] {
  return [...articles].sort((a, b) => {
    const tierA = getJournalTier(a.source);
    const tierB = getJournalTier(b.source);
    if (tierA !== tierB) return tierA - tierB;
    // Same tier: sort by date descending
    return (b.date || "").localeCompare(a.date || "");
  });
}

export function getHomepageArticles(articles: Article[]): Article[] {
  /**
   * Returns articles for homepage display:
   * - All Tier 1-2 articles always included
   * - Fill remaining up to 5 from lower tiers
   * - If Tier 1-2 alone exceeds 5, show all of them
   */
  const sorted = sortByJournalHierarchy(articles);
  const mustShow = sorted.filter(a => getJournalTier(a.source) <= ALWAYS_FRONT_PAGE_TIER);
  const others = sorted.filter(a => getJournalTier(a.source) > ALWAYS_FRONT_PAGE_TIER);

  if (mustShow.length >= 5) {
    return mustShow; // All top-tier, even if > 5
  }
  const remaining = 5 - mustShow.length;
  return [...mustShow, ...others.slice(0, remaining)];
}

export interface Article {
  id: string;
  type: string;
  title: string;
  source: string;
  source_url: string;
  url: string;
  date: string;
  abstract: string;
  authors: string | null;
  image_url: string | null;
  nct_id?: string;
  phase?: string;
  status?: string;
  sponsor?: string;
}

export interface Section {
  label: string;
  color: string;
  articles: Article[];
  commentary?: string;
}

export interface StockData {
  company: string;
  price: number;
  change: number;
  change_pct: number;
  change_6m: number;
  change_6m_pct: number;
  high_6m?: number;
  low_6m?: number;
  market_cap?: string | number;
  pe_ratio?: number;
  target_price?: number;
  recommendation?: string;
  next_earnings_date?: string;
  price_history?: {
    dates: string[];
    closes: number[];
  };
}

export interface PodcastEpisode {
  title: string;
  date: string;
  duration: string;
  mp3_url: string;
  show_notes: string;
  show_notes_html?: string;
  episode_date?: string;
  number?: number;
  guid?: string;
  file_size?: number;
  pub_date_rfc2822?: string;
}

export interface DigestData {
  date: string;
  type?: string;
  executive_summary: string;
  key_points: string[];
  sections: Record<string, Section>;
  stocks: Record<string, StockData>;
  podcast: {
    latest_episode: PodcastEpisode;
    all_episodes?: PodcastEpisode[];
  };
  weekly_digests?: { date: string; file: string }[];
}

export function getLatestDigest(): DigestData {
  const filePath = path.join(process.cwd(), "public", "data", "latest.json");
  try {
    const raw = fs.readFileSync(filePath, "utf-8");
    return JSON.parse(raw);
  } catch {
    // Return safe empty shell so the site never 500s on a missing/corrupt file
    return {
      date: new Date().toISOString().slice(0, 10),
      executive_summary: "",
      key_points: [],
      sections: {},
      stocks: {},
      podcast: { latest_episode: { title: "", date: "", duration: "", mp3_url: "", show_notes: "" } },
    };
  }
}

export function getAllArticles(data: DigestData): Article[] {
  const articles: Article[] = [];
  for (const section of Object.values(data.sections)) {
    articles.push(...section.articles);
  }
  return articles;
}

export function getAllDigestDates(): string[] {
  const digestsDir = path.join(process.cwd(), "public", "data", "digests");
  try {
    const files = fs.readdirSync(digestsDir);
    return files
      .filter((f: string) => f.endsWith(".json"))
      .map((f: string) => f.replace(".json", ""))
      .sort()
      .reverse();
  } catch {
    return [];
  }
}

export function getDigestByDate(dateStr: string): DigestData | null {
  // Validate format to prevent path traversal
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateStr) && !/^weekly-\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    return null;
  }
  const filePath = path.join(process.cwd(), "public", "data", "digests", `${dateStr}.json`);
  try {
    const raw = fs.readFileSync(filePath, "utf-8");
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function getAllHistoricalArticles(): (Article & { digestDate: string; sectionKey: string; sectionColor: string })[] {
  const dates = getAllDigestDates();
  const allArticles: (Article & { digestDate: string; sectionKey: string; sectionColor: string })[] = [];

  for (const date of dates) {
    const digest = getDigestByDate(date);
    if (!digest) continue;
    for (const [key, section] of Object.entries(digest.sections)) {
      for (const article of section.articles) {
        allArticles.push({
          ...article,
          digestDate: date,
          sectionKey: key,
          sectionColor: section.color,
        });
      }
    }
  }

  return allArticles;
}

export function fillEmptySections(data: DigestData): DigestData {
  /**
   * If a section has no articles for today, fill it with the most recent
   * articles from that section across all historical digests.
   * Articles are sorted most recent first.
   */
  const dates = getAllDigestDates();

  for (const [sectionKey, section] of Object.entries(data.sections)) {
    if (section.articles.length > 0) continue;

    // Search historical digests for this section's articles
    const historicalArticles: Article[] = [];
    for (const date of dates) {
      if (date === data.date) continue;
      const digest = getDigestByDate(date);
      if (!digest) continue;
      const histSection = digest.sections[sectionKey];
      if (histSection?.articles?.length) {
        for (const a of histSection.articles) {
          historicalArticles.push({ ...a, date: a.date || date });
        }
      }
      if (historicalArticles.length >= 5) break; // enough to fill the section
    }

    if (historicalArticles.length > 0) {
      section.articles = historicalArticles.slice(0, 5);
    }
  }

  return data;
}

export function getLatestStocksFromHistory(): Record<string, StockData> {
  /**
   * Get the most recent stock data from any digest that has it.
   */
  const dates = getAllDigestDates();
  for (const date of dates) {
    const digest = getDigestByDate(date);
    if (digest?.stocks && Object.keys(digest.stocks).length > 0) {
      return digest.stocks;
    }
  }
  return {};
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T12:00:00");
  return d.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}
