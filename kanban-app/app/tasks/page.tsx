"use client";

import { useEffect, useState, useCallback } from "react";
import { COLUMNS } from "@/lib/types";
import type { Task, Activity, Project } from "@/lib/types";

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [showNew, setShowNew] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newProject, setNewProject] = useState("");
  const [newStatus, setNewStatus] = useState("backlog");
  const [newPriority, setNewPriority] = useState("medium");
  const [filterProject, setFilterProject] = useState<string | null>(null);
  const [dragId, setDragId] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    const [t, a, p] = await Promise.all([
      fetch("/api/tasks").then((r) => r.json()),
      fetch("/api/activity").then((r) => r.json()),
      fetch("/api/projects").then((r) => r.json()),
    ]);
    setTasks(t);
    setActivity(a);
    setProjects(p);
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 10_000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const projectMap = new Map(projects.map((p) => [p.id, p]));

  async function createTask() {
    if (!newTitle.trim()) return;
    await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: newTitle,
        project: newProject,
        status: newStatus,
        priority: newPriority,
      }),
    });
    await fetch("/api/activity", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agent: "user",
        icon: "✚",
        description: `Created task: ${newTitle}`,
        project: newProject,
      }),
    });
    setNewTitle("");
    setShowNew(false);
    fetchAll();
  }

  async function moveTask(id: string, status: string) {
    const task = tasks.find((t) => t.id === id);
    await fetch("/api/tasks", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, status }),
    });
    if (task) {
      await fetch("/api/activity", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent: "user",
          icon: "→",
          description: `Moved "${task.title}" to ${status}`,
          project: task.project,
        }),
      });
    }
    fetchAll();
  }

  async function deleteTask(id: string) {
    await fetch("/api/tasks", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    fetchAll();
  }

  const filtered = filterProject ? tasks.filter((t) => t.project === filterProject) : tasks;

  // Stats
  const total = filtered.length;
  const done = filtered.filter((t) => t.status === "done").length;
  const inProg = filtered.filter((t) => t.status === "in-progress").length;

  return (
    <div className="flex h-full">
      {/* Board */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: "var(--border)" }}>
          <div className="flex items-center gap-3">
            <h1 className="text-[15px] font-semibold">Tasks</h1>
            <div className="flex gap-2 text-[11px]" style={{ color: "var(--text-muted)" }}>
              <span>{total} total</span>
              <span>·</span>
              <span style={{ color: "var(--accent)" }}>{inProg} active</span>
              <span>·</span>
              <span style={{ color: "var(--success)" }}>{done} done</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Project filter chips */}
            <button
              onClick={() => setFilterProject(null)}
              className="px-2 py-0.5 rounded text-[11px] border cursor-pointer"
              style={{
                borderColor: !filterProject ? "var(--accent)" : "var(--border)",
                color: !filterProject ? "var(--accent)" : "var(--text-muted)",
                background: "transparent",
              }}
            >
              All
            </button>
            {projects.slice(0, 8).map((p) => (
              <button
                key={p.id}
                onClick={() => setFilterProject(filterProject === p.id ? null : p.id)}
                className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] border cursor-pointer"
                style={{
                  borderColor: filterProject === p.id ? p.color : "var(--border)",
                  color: filterProject === p.id ? p.color : "var(--text-muted)",
                  background: "transparent",
                }}
              >
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: p.color }} />
                {p.label}
              </button>
            ))}

            <button
              onClick={() => setShowNew(true)}
              className="ml-2 px-3 py-1 rounded text-[12px] font-medium cursor-pointer border-0"
              style={{ background: "var(--accent)", color: "#fff" }}
            >
              + New Task
            </button>
          </div>
        </div>

        {/* Columns */}
        <div className="flex flex-1 gap-2 p-3 overflow-x-auto">
          {COLUMNS.map((col) => {
            const colTasks = filtered.filter((t) => t.status === col.id);
            return (
              <div
                key={col.id}
                className="flex-1 min-w-[240px] max-w-[320px] flex flex-col rounded-lg border"
                style={{ background: "var(--surface)", borderColor: "var(--border)" }}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => {
                  if (dragId) moveTask(dragId, col.id);
                  setDragId(null);
                }}
              >
                <div className="flex items-center justify-between px-3 py-2.5 border-b" style={{ borderColor: "var(--border)" }}>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full" style={{ background: col.dotColor }} />
                    <span className="text-[13px] font-medium">{col.label}</span>
                  </div>
                  <span className="text-[11px] px-1.5 py-0.5 rounded" style={{ background: "var(--bg)", color: "var(--text-muted)" }}>
                    {colTasks.length}
                  </span>
                </div>

                <div className="flex-1 overflow-y-auto p-1.5 flex flex-col gap-1.5">
                  {colTasks.length === 0 && (
                    <div className="text-center py-6 text-[12px]" style={{ color: "var(--text-muted)" }}>
                      No tasks
                    </div>
                  )}
                  {colTasks.map((task) => {
                    const proj = projectMap.get(task.project);
                    return (
                      <div
                        key={task.id}
                        draggable
                        onDragStart={() => setDragId(task.id)}
                        onDragEnd={() => setDragId(null)}
                        className="rounded-md border p-2.5 cursor-grab active:cursor-grabbing transition-colors"
                        style={{
                          background: "var(--bg)",
                          borderColor: "var(--border)",
                          borderLeftWidth: 3,
                          borderLeftColor: proj?.color || "var(--border)",
                          opacity: dragId === task.id ? 0.4 : 1,
                        }}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span
                            className="text-[10px] px-1.5 py-0.5 rounded font-medium uppercase tracking-wide"
                            style={{
                              background: task.type.startsWith("github") ? "rgba(77,126,255,0.15)" : "rgba(255,255,255,0.05)",
                              color: task.type.startsWith("github") ? "var(--accent)" : "var(--text-muted)",
                            }}
                          >
                            {task.type.replace("github-", "")}
                          </span>
                          {task.priority === "urgent" && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded font-medium" style={{ background: "rgba(224,85,85,0.15)", color: "var(--error)" }}>
                              urgent
                            </span>
                          )}
                          {task.priority === "high" && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded font-medium" style={{ background: "rgba(249,115,22,0.15)", color: "var(--warning)" }}>
                              high
                            </span>
                          )}
                        </div>
                        <div className="text-[13px] leading-[1.4] mb-1.5">
                          {task.url ? (
                            <a href={task.url} target="_blank" rel="noopener noreferrer" className="no-underline hover:underline" style={{ color: "var(--text)" }}>
                              {task.title}
                            </a>
                          ) : (
                            task.title
                          )}
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px]" style={{ color: proj?.color || "var(--text-muted)" }}>
                            {proj?.label || task.project}
                          </span>
                          <div className="flex gap-1">
                            {/* Status dot — click to advance */}
                            {col.id !== "done" && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  const nextCol = COLUMNS[COLUMNS.findIndex((c) => c.id === col.id) + 1];
                                  if (nextCol) moveTask(task.id, nextCol.id);
                                }}
                                className="w-4 h-4 rounded-full border-0 cursor-pointer flex items-center justify-center text-[8px]"
                                style={{ background: "var(--surface-hover)", color: "var(--text-muted)" }}
                                title={`Move to ${COLUMNS[COLUMNS.findIndex((c) => c.id === col.id) + 1]?.label}`}
                              >
                                →
                              </button>
                            )}
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteTask(task.id);
                              }}
                              className="w-4 h-4 rounded-full border-0 cursor-pointer flex items-center justify-center text-[8px]"
                              style={{ background: "var(--surface-hover)", color: "var(--text-muted)" }}
                              title="Delete"
                            >
                              ×
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Activity panel */}
      <div className="w-[280px] border-l flex flex-col" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
        <div className="px-3 py-2.5 border-b flex items-center gap-2" style={{ borderColor: "var(--border)" }}>
          <span className="text-[13px] font-medium">Activity</span>
          <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--success)", animation: "pulse 2s infinite" }} />
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {activity.slice(0, 30).map((a) => (
            <div key={a.id} className="flex gap-2 py-2 border-b" style={{ borderColor: "var(--border)" }}>
              <span className="text-[12px] mt-0.5">{a.icon}</span>
              <div className="flex-1 min-w-0">
                <p className="text-[12px] leading-[1.4]" style={{ color: "var(--text-secondary)" }}>
                  {a.description}
                </p>
                <p className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>
                  {new Date(a.timestamp).toLocaleTimeString()}
                  {a.project && <span> · {a.project}</span>}
                </p>
              </div>
            </div>
          ))}
          {activity.length === 0 && (
            <p className="text-center py-6 text-[12px]" style={{ color: "var(--text-muted)" }}>
              No activity yet
            </p>
          )}
        </div>
      </div>

      {/* New task modal */}
      {showNew && (
        <div className="fixed inset-0 flex items-center justify-center z-50" style={{ background: "rgba(0,0,0,0.6)" }}>
          <div className="rounded-lg border p-5 w-[400px]" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
            <h2 className="text-[15px] font-semibold mb-4">New Task</h2>

            <input
              autoFocus
              placeholder="Task title"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && createTask()}
              className="w-full px-3 py-2 rounded border text-[13px] mb-3"
              style={{ background: "var(--bg)", borderColor: "var(--border)", color: "var(--text)", outline: "none" }}
            />

            <div className="flex gap-2 mb-3">
              <select
                value={newProject}
                onChange={(e) => setNewProject(e.target.value)}
                className="flex-1 px-2 py-1.5 rounded border text-[12px]"
                style={{ background: "var(--bg)", borderColor: "var(--border)", color: "var(--text)" }}
              >
                <option value="">No project</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.label}</option>
                ))}
              </select>

              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="px-2 py-1.5 rounded border text-[12px]"
                style={{ background: "var(--bg)", borderColor: "var(--border)", color: "var(--text)" }}
              >
                {COLUMNS.map((c) => (
                  <option key={c.id} value={c.id}>{c.label}</option>
                ))}
              </select>

              <select
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value)}
                className="px-2 py-1.5 rounded border text-[12px]"
                style={{ background: "var(--bg)", borderColor: "var(--border)", color: "var(--text)" }}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowNew(false)}
                className="px-3 py-1.5 rounded text-[12px] border cursor-pointer"
                style={{ background: "transparent", borderColor: "var(--border)", color: "var(--text-secondary)" }}
              >
                Cancel
              </button>
              <button
                onClick={createTask}
                className="px-3 py-1.5 rounded text-[12px] border-0 cursor-pointer font-medium"
                style={{ background: "var(--accent)", color: "#fff" }}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
