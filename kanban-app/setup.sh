#!/bin/bash
# Push kanban-app to the project-kanban GitHub repo
# Usage: bash kanban-app/setup.sh
set -e

TMPDIR=$(mktemp -d)
echo "Cloning project-kanban..."
git clone https://github.com/mbowdish88/project-kanban.git "$TMPDIR/repo"

echo "Copying files..."
cp -r kanban-app/* "$TMPDIR/repo/"
cp -r kanban-app/.gitignore "$TMPDIR/repo/"

cd "$TMPDIR/repo"
git add -A
git commit -m "Initial commit: Next.js kanban board with GitHub auto-discovery

- Next.js 15 + React 19 + Tailwind 4
- Kanban board with 5 columns, drag-drop, project filters
- Projects page with GitHub sync + local folder discovery
- JSON file persistence (zero database)
- Activity feed with 10s live polling
- REST API for agent integration (curl-friendly)

Inspired by openclaw-mission-control"

git push -u origin main

echo ""
echo "Done! Pushed to https://github.com/mbowdish88/project-kanban"
echo ""
echo "To run:"
echo "  cd project-kanban"
echo "  npm install"
echo "  GITHUB_TOKEN=ghp_xxx npm run dev"
echo ""
echo "Clean up: rm -rf $TMPDIR"
