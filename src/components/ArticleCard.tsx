import type { Article } from "@/lib/data";
import Image from "next/image";

interface ArticleCardProps {
  article: Article;
  sectionColor?: string;
}

const TYPE_STYLES: Record<string, string> = {
  Research: "bg-[var(--color-burgundy)] text-[var(--color-cream)]",
  News: "bg-[var(--color-rose)] text-white",
  "Trial Update": "bg-purple-700 text-white",
  Regulatory: "bg-emerald-700 text-white",
  Financial: "bg-amber-700 text-white",
};

const SOURCE_LOGOS: Record<string, string> = {
  "New England Journal of Medicine": "https://www.nejm.org/pb-assets/images/editorial/njm-logo-300x300-1654881279287.png",
  "JACC": "https://www.jacc.org/pb-assets/images/logos/jacc-logo-300x300-1630000000.png",
  "TCTMD": "https://www.tctmd.com/themes/custom/tctmd/favicon/apple-touch-icon.png",
  "Bloomberg": "https://assets.bwbx.io/s3/javelin/public/javelin/images/bloomberg-logo-blue-120x32-1-120x32-3093e4f18b.png",
  "ClinicalTrials.gov": "https://clinicaltrials.gov/ct2/html/images/ct-logo.png",
};

export default function ArticleCard({ article, sectionColor }: ArticleCardProps) {
  const typeStyle = TYPE_STYLES[article.type] || "bg-gray-600 text-white";
  const hasImage = article.image_url;
  const sourceLogo = SOURCE_LOGOS[article.source];

  return (
    <article className="bg-white rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-shadow overflow-hidden">
      <div className={`flex ${hasImage ? "flex-row" : ""}`}>
      <div className="p-5 flex-1">
        {/* Type badge + date */}
        <div className="flex items-center gap-2 mb-3 nav-font">
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
        <div className="nav-font text-xs text-gray-500 mb-3 flex items-center gap-1.5">
          {sourceLogo && (
            <img src={sourceLogo} alt="" className="w-4 h-4 rounded-sm object-contain" />
          )}
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
        <p className="text-sm text-gray-600 leading-relaxed line-clamp-3">
          {article.abstract}
        </p>

        {/* Trial metadata */}
        {article.phase && (
          <div className="mt-3 flex gap-3 nav-font text-xs text-gray-500">
            {article.phase && <span>Phase: <strong>{article.phase}</strong></span>}
            {article.status && <span>Status: <strong>{article.status}</strong></span>}
            {article.sponsor && <span>Sponsor: <strong>{article.sponsor}</strong></span>}
          </div>
        )}
      </div>

        {/* Article image — right side */}
        {hasImage && (
          <div className="w-32 md:w-40 shrink-0 relative hidden sm:block">
            <Image
              src={article.image_url!}
              alt=""
              fill
              className="object-cover"
              sizes="160px"
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
