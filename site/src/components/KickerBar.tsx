import { getLatestDigest } from "@/lib/data";

export default function KickerBar() {
  const data = getLatestDigest();

  // Build stock ticker summary from live data
  const stocks = data.stocks || {};
  const tickerParts = Object.entries(stocks).map(([ticker, info]: [string, any]) => {
    const pct = info?.change_pct ?? 0;
    const arrow = pct >= 0 ? "▲" : "▼";
    return { ticker, arrow, up: pct >= 0 };
  });

  // Use executive summary first sentence as the kicker headline, or fallback
  const execSummary = data.executive_summary || "";
  const firstSentence = execSummary.replace(/<[^>]*>/g, "").split(/[.!?]/)[0]?.trim();
  const kickerText = firstSentence
    ? firstSentence.toUpperCase()
    : "STRUCTURAL HEART DISEASE — RESEARCH, TRIALS & ANALYSIS";

  const today = new Date();
  const timeStr = today.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  });
  const dateStr = today.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).toUpperCase();

  return (
    <div className="kicker-strip">
      <div className="container">
        <div className="kicker-strip-inner">
          <div className="strip-meta">
            <span className="dot" />
            LIVE · {timeStr} · {dateStr}
          </div>
          <div className="kicker-text">
            {kickerText}
          </div>
          <div className="strip-meta">
            {tickerParts.map(({ ticker, arrow, up }) => (
              <span key={ticker}>
                {ticker} <span className={up ? "ticker-up" : "ticker-dn"}>{arrow}</span>
                {" "}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
