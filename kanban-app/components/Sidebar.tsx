"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/tasks", label: "Tasks", icon: "▦" },
  { href: "/projects", label: "Projects", icon: "◈" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed top-0 left-0 h-full w-[180px] border-r flex flex-col"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
      <div className="p-4 border-b" style={{ borderColor: "var(--border)" }}>
        <Link href="/" className="flex items-center gap-2 no-underline">
          <span className="text-lg" style={{ color: "var(--accent)" }}>▦</span>
          <span className="font-semibold text-sm" style={{ color: "var(--text)" }}>
            Project Kanban
          </span>
        </Link>
      </div>

      <nav className="flex-1 p-2 flex flex-col gap-0.5">
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-2.5 px-3 py-2 rounded-md text-[13px] no-underline transition-colors"
              style={{
                background: active ? "var(--surface-hover)" : "transparent",
                color: active ? "var(--text)" : "var(--text-secondary)",
              }}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t text-[11px]" style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
        mbowdish88
      </div>
    </aside>
  );
}
