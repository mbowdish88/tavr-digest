interface ExecutiveSummaryProps {
  summary: string;
}

/** Map topic keywords/phrases to section IDs on the page */
const SECTION_LINKS: [RegExp, string][] = [
  // Aortic — match first to avoid partial matches
  [/\b(TAVR|TAVI|aortic stenosis|aortic valve|transcatheter aortic|balloon-expandable|self-expanding|SAPIEN|Evolut|CoreValve)\b/i, "aortic"],
  // Mitral
  [/\b(MitraClip|Mitra-Clip|PASCAL|TMVR|mitral regurgitation|mitral valve|mitral repair|mitral replacement|TEER|edge-to-edge|COAPT)\b/i, "mitral"],
  // Tricuspid
  [/\b(TriClip|Try-Clip|TTVR|tricuspid|Evoque|TRILUMINATE|TRISCEND)\b/i, "tricuspid"],
  // Surgical comparison
  [/\b(surgical comparison|SAVR|surgery vs|vs\.? surgery|surgical vs|transcatheter vs|compared to surgery|surgical alternative)\b/i, "surgical"],
  // Trials
  [/\b(clinical trial|trial update|PARTNER|NOTION|DEDICATE|EARLY TAVR|EVOLVED|landmark trial)\b/i, "trials"],
  // Regulatory
  [/\b(FDA|regulatory|approval|clearance|CMS|reimbursement)\b/i, "regulatory"],
  // Financial
  [/\b(stock|market cap|Edwards Lifesciences|Medtronic|Abbott|Boston Scientific|financial|earnings|M&A|industry)\b/i, "financial"],
];

function addSectionLinks(html: string): string {
  // Track which sections we've already linked to avoid duplicate links
  const linked = new Set<string>();

  let result = html;
  for (const [pattern, sectionId] of SECTION_LINKS) {
    if (linked.has(sectionId)) continue;

    // Don't link text that's already inside an <a> tag
    result = result.replace(pattern, (match, ...args) => {
      // Check if this match is already inside a link
      const offset = typeof args[args.length - 2] === "number" ? args[args.length - 2] : 0;
      const fullStr = typeof args[args.length - 1] === "string" ? args[args.length - 1] : result;
      const before = fullStr.substring(Math.max(0, offset - 50), offset);
      if (before.includes("<a ") && !before.includes("</a>")) {
        return match; // Already inside a link
      }

      linked.add(sectionId);
      return `<a href="#${sectionId}">${match}</a>`;
    });
  }

  return result;
}

export default function ExecutiveSummary({ summary }: ExecutiveSummaryProps) {
  if (!summary) return null;

  const linkedSummary = addSectionLinks(summary);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6 mb-8">
      <h2 className="nav-font text-base font-bold uppercase tracking-wider text-[var(--color-burgundy)] mb-3">
        Executive Summary
      </h2>
      <p
        className="text-base leading-relaxed text-[var(--color-wine)] [&_a]:text-[var(--color-burgundy)] [&_a]:underline [&_a]:hover:opacity-80"
        dangerouslySetInnerHTML={{ __html: linkedSummary }}
      />
    </div>
  );
}
