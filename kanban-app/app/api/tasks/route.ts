import { NextRequest, NextResponse } from "next/server";
import { readJson, writeJson } from "@/lib/data";
import type { Task } from "@/lib/types";

const FILE = "tasks.json";

// GET /api/tasks — returns all tasks
export async function GET() {
  const tasks = readJson<Task[]>(FILE, []);
  return NextResponse.json(tasks);
}

// POST /api/tasks — create a new task
export async function POST(req: NextRequest) {
  const body = await req.json();
  const tasks = readJson<Task[]>(FILE, []);

  const now = new Date().toISOString();
  const task: Task = {
    id: `t${Date.now()}`,
    title: body.title || "Untitled",
    description: body.description || "",
    status: body.status || "backlog",
    project: body.project || "",
    type: body.type || "task",
    assignee: body.assignee || "",
    priority: body.priority || "medium",
    tags: body.tags || [],
    url: body.url || "",
    createdAt: now,
    updatedAt: now,
  };

  tasks.push(task);
  writeJson(FILE, tasks);

  return NextResponse.json(task, { status: 201 });
}

// PATCH /api/tasks — update a task (requires id in body)
export async function PATCH(req: NextRequest) {
  const body = await req.json();
  if (!body.id) {
    return NextResponse.json({ error: "id required" }, { status: 400 });
  }

  const tasks = readJson<Task[]>(FILE, []);
  const idx = tasks.findIndex((t) => t.id === body.id);
  if (idx === -1) {
    return NextResponse.json({ error: "task not found" }, { status: 404 });
  }

  const { id, ...updates } = body;
  tasks[idx] = { ...tasks[idx], ...updates, updatedAt: new Date().toISOString() };
  writeJson(FILE, tasks);

  return NextResponse.json(tasks[idx]);
}

// DELETE /api/tasks — delete a task (requires id in body)
export async function DELETE(req: NextRequest) {
  const body = await req.json();
  if (!body.id) {
    return NextResponse.json({ error: "id required" }, { status: 400 });
  }

  const tasks = readJson<Task[]>(FILE, []);
  const filtered = tasks.filter((t) => t.id !== body.id);
  if (filtered.length === tasks.length) {
    return NextResponse.json({ error: "task not found" }, { status: 404 });
  }

  writeJson(FILE, filtered);
  return NextResponse.json({ deleted: body.id });
}
