# MEMORY.md — Project Kanban

## Data Schema

### tasks.json
```json
[{
  "id": "t1234567890",
  "title": "string",
  "description": "string",
  "status": "backlog | todo | in-progress | review | done",
  "project": "repo-name",
  "type": "task | bug | feature | github-pr | github-issue | github-workflow",
  "assignee": "string",
  "priority": "low | medium | high | urgent",
  "tags": ["string"],
  "url": "https://...",
  "createdAt": "ISO 8601",
  "updatedAt": "ISO 8601"
}]
```

### activity.json
```json
[{
  "id": "a1234567890",
  "agent": "user | claude | system",
  "icon": "emoji or symbol",
  "description": "What happened",
  "project": "repo-name",
  "timestamp": "ISO 8601"
}]
```

### projects.json
```json
[{
  "id": "repo-name",
  "name": "repo-name",
  "repo": "owner/repo",
  "description": "string",
  "color": "#hex",
  "label": "Short Name",
  "progress": 0-100,
  "status": "active | paused | completed",
  "url": "https://github.com/...",
  "source": "github | local",
  "language": "Python",
  "lastActivity": "ISO 8601"
}]
```

## API Routes

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/tasks | List all tasks |
| POST | /api/tasks | Create task |
| PATCH | /api/tasks | Update task (id required) |
| DELETE | /api/tasks | Delete task (id required) |
| GET | /api/activity | List activity feed |
| POST | /api/activity | Log activity |
| GET | /api/projects | List projects |
| PATCH | /api/projects | Update project |
| GET | /api/github | Discover repos from GitHub + local |

## GitHub Discovery Logic (`/api/github`)

1. Fetches all repos for authenticated user via `GET /user/repos?affiliation=owner`
2. Skips archived repos
3. Auto-assigns colors from PROJECT_COLORS palette
4. Scans PROJECTS_ROOT for local git repos (directories containing `.git/`)
5. Merges: local repos only added if no matching GitHub repo by name
6. Preserves user customizations (color, label, progress) across syncs

## Frontend Polling

All pages use the same pattern:
```tsx
useEffect(() => {
  fetchData();
  const interval = setInterval(fetchData, 10_000);
  return () => clearInterval(interval);
}, []);
```

## File I/O Pattern

`lib/data.ts` provides `readJson(filename, default)` and `writeJson(filename, data)`.
- Auto-creates missing files with default value
- All reads/writes are synchronous (simple, sufficient for single-user)
- Data dir: `<project-root>/data/`

## Lessons

- Next.js API routes run server-side — can access filesystem directly
- Tailwind 4 uses `@import "tailwindcss"` not `@tailwind` directives
- `postcss.config.mjs` needs `@tailwindcss/postcss` plugin
- JSON files should not be gitignored — they ARE the database
- IDs use `t/a/d` prefix + `Date.now()` for uniqueness
