"use client";

import type { StockData } from "@/lib/data";

interface StockTickerProps {
  stocks: Record<string, StockData>;
}

export default function StockTicker({ stocks }: StockTickerProps) {
  return (
    <div className="bg-[#D8D8D8] border-b border-[#CBD5E0] overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 py-2 flex gap-6 overflow-x-auto nav-font text-xs scrollbar-hide">
        {Object.entries(stocks).map(([ticker, data]) => (
          <div key={ticker} className="flex items-center gap-2 whitespace-nowrap">
            <span className="font-bold text-[#1B2A4A]">{ticker}</span>
            <span className="text-[#4A5568]">${data.price.toFixed(2)}</span>
            <span
              className={`font-semibold ${
                data.change_pct >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {data.change_pct >= 0 ? "+" : ""}
              {data.change_pct.toFixed(2)}%
            </span>
            <span className="text-[#A0AEC0]">|</span>
            <span
              className={`text-[10px] ${
                data.change_6m_pct >= 0 ? "text-green-600/70" : "text-red-600/70"
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
