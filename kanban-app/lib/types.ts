export interface Task {
  id: string;
  title: string;
  description: string;
  status: "backlog" | "todo" | "in-progress" | "review" | "done";
  project: string;
  type: "task" | "bug" | "feature" | "github-pr" | "github-issue" | "github-workflow";
  assignee: string;
  priority: "low" | "medium" | "high" | "urgent";
  tags: string[];
  url: string;
  createdAt: string;
  updatedAt: string;
}

export interface Activity {
  id: string;
  agent: string;
  icon: string;
  description: string;
  project: string;
  timestamp: string;
}

export interface Project {
  id: string;
  name: string;
  repo: string;
  description: string;
  color: string;
  label: string;
  progress: number;
  status: "active" | "paused" | "completed";
  url: string;
  source: "github" | "local";
  language: string;
  lastActivity: string;
}

export interface Column {
  id: string;
  label: string;
  dotColor: string;
}

export const COLUMNS: Column[] = [
  { id: "backlog", label: "Backlog", dotColor: "#555" },
  { id: "todo", label: "To Do", dotColor: "#f97316" },
  { id: "in-progress", label: "In Progress", dotColor: "#4d7eff" },
  { id: "review", label: "Review", dotColor: "#a855f7" },
  { id: "done", label: "Done", dotColor: "#22c55e" },
];

// Auto-assigned colors for discovered projects
export const PROJECT_COLORS = [
  "#C4787A", "#4A90D9", "#50C878", "#F5A623", "#9B59B6",
  "#1DB954", "#E74C3C", "#3498DB", "#E67E22", "#1ABC9C",
  "#E84393", "#6C5CE7", "#00B894", "#FDCB6E", "#74B9FF",
];
