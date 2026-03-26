#!/bin/bash
# Sync tavr-digest with GitHub
# Run this when you sit down at a machine or before you walk away

cd "$(dirname "$0")" || exit 1

echo "=== Syncing tavr-digest ==="

# Pull latest from GitHub
echo "Pulling latest..."
git pull --rebase origin main || { echo "Pull failed — resolve conflicts first"; exit 1; }

# If there are local changes, commit and push them
if [ -n "$(git status --porcelain)" ]; then
    echo "Local changes detected, pushing..."
    git add -A
    git commit -m "Sync local changes from $(hostname) on $(date '+%Y-%m-%d %H:%M')"
    git push origin main || { echo "Push failed"; exit 1; }
    echo "Changes pushed."
else
    echo "Already up to date."
fi

echo "=== Done ==="
