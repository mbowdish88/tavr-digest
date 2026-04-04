import type { Article } from "@/lib/data";

interface ArticleCardProps {
  article: Article;
  sectionColor?: string;
  fullAbstract?: boolean;
}

const TYPE_STYLES: Record<string, string> = {
  Research: "bg-[var(--color-burgundy)] text-[var(--color-cream)]",
  News: "bg-[var(--color-rose)] text-white",
  "Trial Update": "bg-purple-700 text-white",
  Regulatory: "bg-emerald-700 text-white",
  Financial: "bg-amber-700 text-white",
};

/** Journal abbreviation/color for the visual accent block */
function getJournalBranding(source: string): { abbrev: string; bg: string; text: string } | null {
  const s = source.toLowerCase();
  if (s.includes("new england") || s.includes("nejm") || s === "n engl j med")
    return { abbrev: "NEJM", bg: "bg-red-800", text: "text-white" };
  if (s.includes("jama") && !s.includes("cardiol"))
    return { abbrev: "JAMA", bg: "bg-blue-900", text: "text-white" };
  if (s.includes("jacc") && s.includes("interv"))
    return { abbrev: "JACC:CI", bg: "bg-amber-700", text: "text-white" };
  if (s.includes("jacc") || s.includes("j am coll cardiol"))
    return { abbrev: "JACC", bg: "bg-amber-800", text: "text-white" };
  if (s.includes("lancet"))
    return { abbrev: "Lancet", bg: "bg-blue-700", text: "text-white" };
  if (s.includes("european heart") || s.includes("eur heart") || s === "ehj")
    return { abbrev: "EHJ", bg: "bg-indigo-800", text: "text-white" };
  if (s.includes("circulation"))
    return { abbrev: "Circ", bg: "bg-red-700", text: "text-white" };
  if (s.includes("annals of thoracic") || s.includes("ann thorac"))
    return { abbrev: "ATS", bg: "bg-slate-700", text: "text-white" };
  if (s.includes("jtcvs") || s.includes("j thorac cardiovasc"))
    return { abbrev: "JTCVS", bg: "bg-slate-800", text: "text-white" };
  if (s.includes("ejcts") || s.includes("eur j cardiothorac"))
    return { abbrev: "EJCTS", bg: "bg-slate-600", text: "text-white" };
  if (s.includes("tctmd"))
    return { abbrev: "TCTMD", bg: "bg-sky-700", text: "text-white" };
  if (s.includes("fda"))
    return { abbrev: "FDA", bg: "bg-emerald-800", text: "text-white" };
  if (s.includes("clinicaltrials"))
    return { abbrev: "CT.gov", bg: "bg-purple-800", text: "text-white" };
  if (s.includes("biorxiv") || s.includes("medrxiv"))
    return { abbrev: "preprint", bg: "bg-orange-600", text: "text-white" };
  return null;
}

/** Tier 1-2 journals get a subtle warm background to signal importance */
const TIER1_ABBREVS = new Set(["NEJM", "JAMA", "JACC", "Lancet", "EHJ", "JACC:CI"]);

function isTier1(branding: { abbrev: string } | null): boolean {
  return branding !== null && TIER1_ABBREVS.has(branding.abbrev);
}

export default function ArticleCard({ article, sectionColor, fullAbstract = false }: ArticleCardProps) {
  const typeStyle = TYPE_STYLES[article.type] || "bg-gray-600 text-white";
  const hasImage = article.image_url;
  const branding = getJournalBranding(article.source);
  const tier1 = isTier1(branding);

  return (
    <article
      className={`rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-shadow overflow-hidden ${
        tier1 ? "bg-[var(--color-surface-alt)]" : "bg-white"
      }`}
    >
      <div className="flex flex-row">
        {/* Journal branding accent — left side panel (sm and up) */}
        {branding && !hasImage && (
          <div className={`w-16 md:w-20 shrink-0 ${branding.bg} hidden sm:flex items-center justify-center`}>
            <span className={`nav-font text-xs md:text-sm font-bold ${branding.text} text-center leading-tight`}>
              {branding.abbrev}
            </span>
          </div>
        )}

        <div className="p-5 flex-1 min-w-0">
          {/* Mobile-only: journal badge as inline pill above title */}
          {branding && !hasImage && (
            <div className="sm:hidden mb-2">
              <span className={`nav-font inline-block text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${branding.bg} ${branding.text}`}>
                {branding.abbrev}
              </span>
            </div>
          )}

          {/* Type badge + date */}
          <div className="flex items-center gap-2 mb-3 nav-font flex-wrap">
            <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${typeStyle}`}>
              {article.type}
            </span>
            <span className="text-xs text-gray-400">{article.date}</span>
            {article.nct_id && (
              <a
                href={`https://clinicaltrials.gov/study/${article.nct_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] font-mono text-[var(--color-rose)] hover:underline"
              >
                {article.nct_id}
              </a>
            )}
          </div>

          {/* Title */}
          <h3 className="text-lg font-semibold leading-snug mb-2">
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--color-wine)] hover:text-[var(--color-rose)] transition-colors"
            >
              {article.title}
            </a>
          </h3>

          {/* Source + Authors */}
          <div className="nav-font text-xs text-gray-500 mb-3 flex items-center gap-1.5 flex-wrap">
            <a
              href={article.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-[var(--color-burgundy)] hover:underline"
            >
              {article.source}
            </a>
            {article.authors && (
              <span className="ml-1">— {article.authors}</span>
            )}
          </div>

          {/* Abstract */}
          {article.abstract && article.abstract !== "No abstract available." && (
            <p className={`text-sm text-gray-600 leading-relaxed ${fullAbstract ? "" : "line-clamp-3"}`}>
              {article.abstract}
            </p>
          )}

          {/* Trial metadata */}
          {article.phase && (
            <div className="mt-3 flex gap-3 nav-font text-xs text-gray-500 flex-wrap">
              {article.phase && <span>Phase: <strong>{article.phase}</strong></span>}
              {article.status && <span>Status: <strong>{article.status}</strong></span>}
              {article.sponsor && <span>Sponsor: <strong>{article.sponsor}</strong></span>}
            </div>
          )}
        </div>

        {/* Article image — right side (only if real image exists) */}
        {hasImage && (
          <div className="w-32 md:w-40 shrink-0 relative hidden sm:block">
            <img
              src={article.image_url!}
              alt=""
              className="absolute inset-0 w-full h-full object-cover"
            />
          </div>
        )}
      </div>

      {/* Section color bar */}
      {sectionColor && (
        <div className="h-1" style={{ backgroundColor: sectionColor }} />
      )}
    </article>
  );
}
