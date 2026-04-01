"use client";

import { useEffect, useState, useCallback } from "react";
import type { Project } from "@/lib/types";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [syncing, setSyncing] = useState(false);

  const fetchProjects = useCallback(async () => {
    const data = await fetch("/api/projects").then((r) => r.json());
    setProjects(data);
  }, []);

  async function syncGitHub() {
    setSyncing(true);
    await fetch("/api/github");
    await fetchProjects();
    setSyncing(false);
  }

  useEffect(() => {
    fetchProjects();
    const interval = setInterval(fetchProjects, 10_000);
    return () => clearInterval(interval);
  }, [fetchProjects]);

  const active = projects.filter((p) => p.status === "active");
  const paused = projects.filter((p) => p.status === "paused");
  const completed = projects.filter((p) => p.status === "completed");

  return (
    <div className="p-6 max-w-[1100px]">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[18px] font-semibold mb-1">Projects</h1>
          <p className="text-[13px]" style={{ color: "var(--text-secondary)" }}>
            {projects.length} projects discovered
          </p>
        </div>
        <button
          onClick={syncGitHub}
          disabled={syncing}
          className="px-3 py-1.5 rounded text-[12px] font-medium border cursor-pointer"
          style={{
            background: syncing ? "var(--surface-hover)" : "transparent",
            borderColor: "var(--border)",
            color: syncing ? "var(--text-muted)" : "var(--accent)",
          }}
        >
          {syncing ? "Syncing..." : "Sync GitHub"}
        </button>
      </div>

      {active.length > 0 && (
        <Section title="Active" projects={active} onUpdate={fetchProjects} />
      )}
      {paused.length > 0 && (
        <Section title="Paused" projects={paused} onUpdate={fetchProjects} />
      )}
      {completed.length > 0 && (
        <Section title="Completed" projects={completed} onUpdate={fetchProjects} />
      )}
      {projects.length === 0 && (
        <div className="text-center py-16">
          <p className="text-[14px] mb-3" style={{ color: "var(--text-secondary)" }}>
            No projects yet
          </p>
          <button
            onClick={syncGitHub}
            className="px-4 py-2 rounded text-[13px] font-medium border-0 cursor-pointer"
            style={{ background: "var(--accent)", color: "#fff" }}
          >
            Sync from GitHub
          </button>
        </div>
      )}
    </div>
  );
}

function Section({ title, projects, onUpdate }: { title: string; projects: Project[]; onUpdate: () => void }) {
  async function toggleStatus(id: string, current: string) {
    const next = current === "active" ? "paused" : "active";
    await fetch("/api/projects", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, status: next }),
    });
    onUpdate();
  }

  return (
    <div className="mb-6">
      <h2 className="text-[12px] font-medium uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>
        {title} ({projects.length})
      </h2>
      <div className="flex flex-col gap-2">
        {projects.map((p) => (
          <div
            key={p.id}
            className="flex items-center gap-4 px-4 py-3 rounded-lg border transition-colors"
            style={{
              background: "var(--surface)",
              borderColor: "var(--border)",
              borderLeftWidth: 4,
              borderLeftColor: p.color,
            }}
          >
            {/* Color dot + Name */}
            <div style={{ width: 220, flexShrink: 0 }}>
              <div className="flex items-center gap-2 mb-0.5">
                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: p.color }} />
                <span className="text-[14px] font-medium" style={{ color: "var(--text)" }}>
                  {p.label || p.name}
                </span>
              </div>
              <p className="text-[12px] truncate ml-4" style={{ color: "var(--text-secondary)" }}>
                {p.description || p.repo}
              </p>
            </div>

            {/* Badges */}
            <div className="flex items-center gap-1.5 flex-shrink-0">
              {p.language && (
                <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: "var(--bg)", color: "var(--text-muted)" }}>
                  {p.language}
                </span>
              )}
              {p.source === "local" && (
                <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: "rgba(249,115,22,0.15)", color: "var(--warning)" }}>
                  local
                </span>
              )}
            </div>

            {/* Spacer */}
            <div className="flex-1" />

            {/* Progress bar */}
            <div className="w-28 flex-shrink-0">
              <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "var(--bg)" }}>
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${Math.max(p.progress, 2)}%`, background: p.color }}
                />
              </div>
              <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                {p.progress}%
              </span>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1.5 flex-shrink-0">
              {p.url && (
                <a
                  href={p.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-2 py-1 rounded text-[11px] border no-underline"
                  style={{ borderColor: "var(--border)", color: "var(--text-muted)", background: "transparent" }}
                >
                  GitHub
                </a>
              )}
              <button
                onClick={() => toggleStatus(p.id, p.status)}
                className="px-2 py-1 rounded text-[11px] border cursor-pointer"
                style={{ borderColor: "var(--border)", color: "var(--text-muted)", background: "transparent" }}
              >
                {p.status === "active" ? "Pause" : "Activate"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
