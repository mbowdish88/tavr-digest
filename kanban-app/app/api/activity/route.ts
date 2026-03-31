import { NextRequest, NextResponse } from "next/server";
import { readJson, writeJson } from "@/lib/data";
import type { Activity } from "@/lib/types";

const FILE = "activity.json";
const MAX_ENTRIES = 100;

// GET /api/activity — returns activity feed (newest first)
export async function GET() {
  const activities = readJson<Activity[]>(FILE, []);
  return NextResponse.json(activities);
}

// POST /api/activity — log a new activity
export async function POST(req: NextRequest) {
  const body = await req.json();
  const activities = readJson<Activity[]>(FILE, []);

  const entry: Activity = {
    id: `a${Date.now()}`,
    agent: body.agent || "system",
    icon: body.icon || "●",
    description: body.description || "",
    project: body.project || "",
    timestamp: new Date().toISOString(),
  };

  activities.unshift(entry);
  if (activities.length > MAX_ENTRIES) {
    activities.length = MAX_ENTRIES;
  }
  writeJson(FILE, activities);

  return NextResponse.json(entry, { status: 201 });
}
