import type { Article } from "@/lib/data";

interface ArticleCardProps {
  article: Article;
  sectionColor?: string;
  fullAbstract?: boolean;
}

function getJournalAbbrev(source: string): string | null {
  const s = source.toLowerCase();
  if (s.includes("new england") || s.includes("nejm") || s === "n engl j med") return "NEJM";
  if (s.includes("jama") && !s.includes("cardiol")) return "JAMA";
  if (s.includes("jacc") && s.includes("interv")) return "JACC:CI";
  if (s.includes("jacc") || s.includes("j am coll cardiol")) return "JACC";
  if (s.includes("lancet")) return "Lancet";
  if (s.includes("european heart") || s.includes("eur heart") || s === "ehj") return "EHJ";
  if (s.includes("circulation")) return "Circ";
  if (s.includes("annals of thoracic") || s.includes("ann thorac")) return "ATS";
  if (s.includes("jtcvs") || s.includes("j thorac cardiovasc")) return "JTCVS";
  if (s.includes("ejcts") || s.includes("eur j cardiothorac")) return "EJCTS";
  if (s.includes("tctmd")) return "TCTMD";
  if (s.includes("fda")) return "FDA";
  if (s.includes("clinicaltrials")) return "CT.gov";
  if (s.includes("biorxiv") || s.includes("medrxiv")) return "preprint";
  return null;
}

function isTier1(source: string): boolean {
  const s = source.toLowerCase();
  return (
    s.includes("new england") || s.includes("nejm") || s === "n engl j med" ||
    (s.includes("jama") && !s.includes("cardiol")) ||
    s.includes("jacc") || s.includes("j am coll cardiol") ||
    s.includes("lancet")
  );
}

export default function ArticleCard({ article, fullAbstract = false }: ArticleCardProps) {
  const abbrev = getJournalAbbrev(article.source);
  const tier1 = isTier1(article.source);
  const hasAbstract = article.abstract && article.abstract !== "No abstract available." && article.abstract.trim() !== "";

  return (
    <article style={{ padding: "16px 0" }}>
      {/* Metadata line */}
      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
        {abbrev && (
          <span
            className="nav-font uppercase"
            style={{
              fontSize: "11px",
              letterSpacing: "0.05em",
              color: "var(--color-accent)",
            }}
          >
            {abbrev}
          </span>
        )}
        <span
          className="nav-font uppercase"
          style={{ fontSize: "11px", color: "var(--color-muted)", letterSpacing: "0.05em" }}
        >
          {article.type}
        </span>
        <span className="nav-font" style={{ fontSize: "11px", color: "var(--color-muted)" }}>
          &middot;
        </span>
        <span className="nav-font" style={{ fontSize: "11px", color: "var(--color-muted)" }}>
          {article.date}
        </span>
        {article.nct_id && (
          <>
            <span className="nav-font" style={{ fontSize: "11px", color: "var(--color-muted)" }}>&middot;</span>
            <a
              href={`https://clinicaltrials.gov/study/${article.nct_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="nav-font font-mono hover:underline"
              style={{ fontSize: "10px", color: "var(--color-accent)" }}
            >
              {article.nct_id}
            </a>
          </>
        )}
      </div>

      {/* Title */}
      <h3
        className="leading-snug mb-1.5"
        style={{
          fontFamily: "var(--font-playfair), 'Playfair Display', Georgia, serif",
          fontSize: tier1 ? "20px" : "18px",
          fontWeight: 400,
          color: "var(--color-ink)",
        }}
      >
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:underline"
          style={{ color: "var(--color-ink)", textDecoration: "none" }}
        >
          {article.title}
        </a>
      </h3>

      {/* Source + Authors */}
      <div className="nav-font mb-2" style={{ fontSize: "12px", color: "var(--color-muted)" }}>
        <a
          href={article.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:underline"
          style={{ color: "var(--color-muted)" }}
        >
          {article.source}
        </a>
        {article.authors && (
          <span> &middot; {article.authors}</span>
        )}
      </div>

      {/* Abstract */}
      {hasAbstract && (
        <p
          className={fullAbstract ? "" : "line-clamp-2"}
          style={{
            fontFamily: "Georgia, serif",
            fontSize: "14px",
            color: "var(--color-muted)",
            lineHeight: "1.6",
          }}
        >
          {article.abstract}
        </p>
      )}

      {/* Trial metadata */}
      {article.phase && (
        <div className="mt-2 flex gap-3 flex-wrap" style={{ fontSize: "12px", color: "var(--color-muted)" }}>
          {article.phase && <span className="nav-font">Phase: <strong>{article.phase}</strong></span>}
          {article.status && <span className="nav-font">Status: <strong>{article.status}</strong></span>}
          {article.sponsor && <span className="nav-font">Sponsor: <strong>{article.sponsor}</strong></span>}
        </div>
      )}

      {/* Read more */}
      <div className="mt-2">
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="nav-font hover:underline"
          style={{ fontSize: "13px", color: "var(--color-accent)", textDecoration: "none" }}
        >
          Read more &rarr;
        </a>
      </div>
    </article>
  );
}
