"use client";

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

interface StockChartProps {
  ticker: string;
  company: string;
  price: number;
  change_pct: number;
  change_6m_pct: number;
  price_history?: {
    dates: string[];
    closes: number[];
  };
}

export default function StockChart({
  ticker,
  company,
  price,
  change_pct,
  change_6m_pct,
  price_history,
}: StockChartProps) {
  const hasHistory = (price_history?.dates?.length ?? 0) > 0;
  const lineColor = change_6m_pct >= 0 ? "#16a34a" : "#dc2626";

  const chartData = hasHistory
    ? price_history!.dates.map((date, i) => ({
        date,
        price: price_history!.closes[i],
      }))
    : [];

  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="flex items-center justify-between mb-1">
        <div>
          <span className="nav-font text-sm font-bold text-[var(--color-wine)]">{ticker}</span>
          <p className="text-[10px] text-gray-400">{company}</p>
        </div>
        <div className="text-right">
          <span className="nav-font text-base font-semibold">${price.toFixed(2)}</span>
          <p
            className={`nav-font text-[10px] font-semibold ${
              change_pct >= 0 ? "text-green-600" : "text-red-600"
            }`}
          >
            {change_pct >= 0 ? "+" : ""}
            {change_pct.toFixed(2)}% today
          </p>
        </div>
      </div>

      {hasHistory && (
        <div className="mt-1" style={{ height: 60 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <XAxis dataKey="date" hide />
              <YAxis domain={["dataMin", "dataMax"]} hide />
              <Tooltip
                contentStyle={{
                  fontSize: 11,
                  fontFamily: "Arial, sans-serif",
                  padding: "4px 8px",
                  borderRadius: 4,
                  border: "1px solid #e5e7eb",
                }}
                labelStyle={{ fontSize: 10, color: "#718096" }}
              />
              <Line
                type="monotone"
                dataKey="price"
                stroke={lineColor}
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="flex justify-between nav-font text-[10px] mt-1 text-gray-400">
        <span className={change_6m_pct >= 0 ? "text-green-600" : "text-red-600"}>
          6M: {change_6m_pct >= 0 ? "+" : ""}{change_6m_pct.toFixed(1)}%
        </span>
        {hasHistory && <span>6-month chart</span>}
      </div>
    </div>
  );
}
