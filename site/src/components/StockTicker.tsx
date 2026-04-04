"use client";

import type { StockData } from "@/lib/data";

interface StockTickerProps {
  stocks: Record<string, StockData>;
}

export default function StockTicker({ stocks }: StockTickerProps) {
  return (
    <div className="bg-[#1B2A4A] border-b border-[#3D5873] overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 py-2 flex gap-6 overflow-x-auto nav-font text-xs scrollbar-hide">
        {Object.entries(stocks).map(([ticker, data]) => (
          <div key={ticker} className="flex items-center gap-2 whitespace-nowrap">
            <span className="font-bold text-[#EDE0C4]">{ticker}</span>
            <span className="font-mono text-white/90">${data.price.toFixed(2)}</span>
            <span
              className={`font-mono font-semibold ${
                data.change_pct >= 0 ? "text-green-400" : "text-red-400"
              }`}
            >
              {data.change_pct >= 0 ? "+" : ""}
              {data.change_pct.toFixed(2)}%
            </span>
            <span className="text-white/20">|</span>
            <span
              className={`font-mono text-[10px] ${
                data.change_6m_pct >= 0 ? "text-green-400/70" : "text-red-400/70"
              }`}
            >
              6M: {data.change_6m_pct >= 0 ? "+" : ""}
              {data.change_6m_pct.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
