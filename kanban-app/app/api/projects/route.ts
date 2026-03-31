import { NextRequest, NextResponse } from "next/server";
import { readJson, writeJson } from "@/lib/data";
import type { Project } from "@/lib/types";

const FILE = "projects.json";

// GET /api/projects — returns all projects
export async function GET() {
  const projects = readJson<Project[]>(FILE, []);
  return NextResponse.json(projects);
}

// PATCH /api/projects — update a project (requires id in body)
export async function PATCH(req: NextRequest) {
  const body = await req.json();
  if (!body.id) {
    return NextResponse.json({ error: "id required" }, { status: 400 });
  }

  const projects = readJson<Project[]>(FILE, []);
  const idx = projects.findIndex((p) => p.id === body.id);
  if (idx === -1) {
    return NextResponse.json({ error: "project not found" }, { status: 404 });
  }

  const { id, ...updates } = body;
  projects[idx] = { ...projects[idx], ...updates };
  writeJson(FILE, projects);

  return NextResponse.json(projects[idx]);
}
