# CLAUDE.md — Project Kanban

Real-time kanban board that auto-discovers and tracks all GitHub projects + local repos.

## Quick Start

```bash
npm install
GITHUB_TOKEN=ghp_xxx npm run dev
# Open http://localhost:3000
```

## Env Vars

- `GITHUB_TOKEN` — GitHub personal access token (repo scope for private repos)
- `GITHUB_USERNAME` — GitHub username (optional, uses token owner by default)
- `PROJECTS_ROOT` — Path to local projects folder (e.g. `/Users/mbowdish`). Scans for git repos.

## Architecture

Next.js 15 + React 19 + Tailwind 4. Inspired by [openclaw-mission-control](https://github.com/dmitrymindstudio/openclaw-mission-control).

```
kanban-app/
├── app/
│   ├── layout.tsx              # Root shell (sidebar + header)
│   ├── page.tsx                # Redirects to /tasks
│   ├── tasks/page.tsx          # Kanban board (5 columns, drag-drop, filters)
│   ├── projects/page.tsx       # Projects overview (progress, GitHub sync)
│   └── api/
│       ├── tasks/route.ts      # GET/POST/PATCH/DELETE tasks
│       ├── activity/route.ts   # GET/POST activity feed
│       ├── projects/route.ts   # GET/PATCH projects
│       └── github/route.ts     # GET — discover repos from GitHub + local folder
├── components/
│   ├── Sidebar.tsx             # Navigation
│   └── Header.tsx              # Live indicator, pause button
├── lib/
│   ├── types.ts                # TypeScript types, column definitions
│   └── data.ts                 # JSON file read/write helpers
└── data/
    ├── tasks.json              # Task state (kanban cards)
    ├── activity.json           # Activity feed (max 100 entries)
    └── projects.json           # Discovered projects
```

## Key Patterns

- **Zero database** — all state is flat JSON files in `data/`
- **10s polling** — frontend polls API every 10 seconds for live updates
- **Dual access** — both UI and agents can modify data via HTTP API
- **Dynamic discovery** — `GET /api/github` auto-discovers all GitHub repos + local git folders
- **Drag-and-drop** — tasks can be dragged between columns
- **Activity logging** — every action creates an activity entry visible in the right panel

## API Reference

### Tasks
```bash
curl http://localhost:3000/api/tasks                              # List all
curl -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Fix bug","project":"tavr-digest","status":"todo","priority":"high"}'
curl -X PATCH http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"id":"t123","status":"in-progress"}'
curl -X DELETE http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"id":"t123"}'
```

### Activity
```bash
curl http://localhost:3000/api/activity                           # List feed
curl -X POST http://localhost:3000/api/activity \
  -H "Content-Type: application/json" \
  -d '{"agent":"claude","icon":"🤖","description":"Deployed v2.1","project":"tavr-digest"}'
```

### Projects
```bash
curl http://localhost:3000/api/projects                           # List all
curl http://localhost:3000/api/github                             # Sync from GitHub + local
curl -X PATCH http://localhost:3000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"id":"tavr-digest","progress":75,"status":"active"}'
```

## Kanban Columns

Backlog → To Do → In Progress → Review → Done

## Adding Features

- New pages: create `app/<name>/page.tsx` and add nav item to `components/Sidebar.tsx`
- New API: create `app/api/<name>/route.ts` with GET/POST handlers
- New data: add JSON file in `data/` and types in `lib/types.ts`
