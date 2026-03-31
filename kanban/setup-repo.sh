#!/bin/bash
# Run this from your local machine to push kanban files to project-kanban repo
set -e

TMPDIR=$(mktemp -d)
echo "Working in $TMPDIR"

git clone https://github.com/mbowdish88/project-kanban.git "$TMPDIR/project-kanban"
cd "$TMPDIR/project-kanban"

mkdir -p kanban .github/workflows

# Copy files from tavr-digest feature branch
TAVR_DIR="${1:-$(cd ~ && pwd)/tavr-digest}"
git -C "$TAVR_DIR" checkout claude/kanban-board-realtime-0yM9J 2>/dev/null || true

cp "$TAVR_DIR/kanban/standalone/CLAUDE.md" ./CLAUDE.md
cp "$TAVR_DIR/kanban/standalone/MEMORY.md" ./MEMORY.md
cp "$TAVR_DIR/kanban/__init__.py" ./kanban/
cp "$TAVR_DIR/kanban/board.py" ./kanban/
cp "$TAVR_DIR/kanban/board.html" ./kanban/
cp "$TAVR_DIR/.github/workflows/kanban-update.yml" ./.github/workflows/

git add -A
git commit -m "Initial commit: real-time kanban board"
git push -u origin main

echo ""
echo "Done! Files pushed to https://github.com/mbowdish88/project-kanban"
echo "Clean up: rm -rf $TMPDIR"
