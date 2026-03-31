import { NextResponse } from "next/server";
import { readdirSync, existsSync, statSync } from "fs";
import { join } from "path";
import { readJson, writeJson } from "@/lib/data";
import type { Project } from "@/lib/types";
import { PROJECT_COLORS } from "@/lib/types";

const GITHUB_API = "https://api.github.com";

function headers(token: string) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
}

async function fetchGitHubRepos(token: string, username: string): Promise<Project[]> {
  const projects: Project[] = [];
  let page = 1;

  while (true) {
    const resp = await fetch(
      `${GITHUB_API}/user/repos?per_page=100&page=${page}&sort=updated&affiliation=owner`,
      { headers: headers(token), next: { revalidate: 0 } }
    );
    if (!resp.ok) break;
    const repos = await resp.json();
    if (!Array.isArray(repos) || repos.length === 0) break;

    for (const repo of repos) {
      if (repo.archived) continue;
      projects.push({
        id: repo.name,
        name: repo.name,
        repo: repo.full_name,
        description: repo.description || "",
        color: PROJECT_COLORS[projects.length % PROJECT_COLORS.length],
        label: repo.name.replace(/[-_]/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()).slice(0, 16),
        progress: 0,
        status: "active",
        url: repo.html_url,
        source: "github",
        language: repo.language || "",
        lastActivity: repo.updated_at || "",
      });
    }
    page++;
  }

  return projects;
}

function discoverLocalProjects(rootDir: string): Project[] {
  const projects: Project[] = [];
  if (!existsSync(rootDir)) return projects;

  for (const entry of readdirSync(rootDir)) {
    const fullPath = join(rootDir, entry);
    try {
      if (!statSync(fullPath).isDirectory()) continue;
      if (entry.startsWith(".")) continue;
      if (!existsSync(join(fullPath, ".git"))) continue;

      projects.push({
        id: `local-${entry}`,
        name: entry,
        repo: "",
        description: `Local project at ${fullPath}`,
        color: PROJECT_COLORS[projects.length % PROJECT_COLORS.length],
        label: entry.replace(/[-_]/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()).slice(0, 16),
        progress: 0,
        status: "active",
        url: "",
        source: "local",
        language: "",
        lastActivity: statSync(fullPath).mtime.toISOString(),
      });
    } catch {
      // skip inaccessible dirs
    }
  }

  return projects;
}

// GET /api/github — discover repos from GitHub + local projects folder
export async function GET() {
  const token = process.env.GITHUB_TOKEN || "";
  const username = process.env.GITHUB_USERNAME || "";
  const projectsRoot = process.env.PROJECTS_ROOT || "";

  const allProjects: Project[] = [];

  // Fetch from GitHub
  if (token) {
    try {
      const ghProjects = await fetchGitHubRepos(token, username);
      allProjects.push(...ghProjects);
    } catch (e) {
      console.error("GitHub fetch error:", e);
    }
  }

  // Discover local projects
  if (projectsRoot) {
    const localProjects = discoverLocalProjects(projectsRoot);
    // Merge: skip locals that match a GitHub repo name
    const ghNames = new Set(allProjects.map((p) => p.name));
    for (const lp of localProjects) {
      if (!ghNames.has(lp.name)) {
        allProjects.push(lp);
      }
    }
  }

  // Persist discovered projects (merge with existing, preserve colors/progress)
  const existing = readJson<Project[]>("projects.json", []);
  const existingMap = new Map(existing.map((p) => [p.id, p]));

  const merged = allProjects.map((p) => {
    const prev = existingMap.get(p.id);
    if (prev) {
      return { ...p, color: prev.color, label: prev.label, progress: prev.progress, status: prev.status };
    }
    return p;
  });

  writeJson("projects.json", merged);

  return NextResponse.json({ projects: merged, discoveredAt: new Date().toISOString() });
}
