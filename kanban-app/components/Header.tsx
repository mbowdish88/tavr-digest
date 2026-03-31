"use client";

import { useEffect, useState } from "react";

export default function Header() {
  const [lastUpdate, setLastUpdate] = useState<string>("");
  const [live, setLive] = useState(true);

  useEffect(() => {
    const tick = () => setLastUpdate(new Date().toLocaleTimeString());
    tick();
    const interval = setInterval(tick, 10_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header
      className="fixed top-0 left-[180px] right-0 h-[44px] flex items-center justify-between px-4 border-b z-10"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <span
            className="w-2 h-2 rounded-full"
            style={{
              background: live ? "var(--success)" : "var(--text-muted)",
              animation: live ? "pulse 2s infinite" : "none",
            }}
          />
          <span className="text-[11px] font-medium tracking-wide" style={{ color: live ? "var(--success)" : "var(--text-muted)" }}>
            LIVE
          </span>
        </div>
        <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
          {lastUpdate}
        </span>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setLive(!live)}
          className="px-2.5 py-1 rounded text-[11px] font-medium border cursor-pointer transition-colors"
          style={{
            background: "transparent",
            borderColor: "var(--border)",
            color: live ? "var(--text-secondary)" : "var(--warning)",
          }}
        >
          {live ? "Pause" : "Resume"}
        </button>
      </div>
    </header>
  );
}
