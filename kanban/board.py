"""Kanban board data generator.

Queries GitHub API across all projects and builds a kanban JSON structure.
Pushes the result to thevalvewire-site for Vercel deployment.

Usage:
    python -m kanban.board          # Generate and push kanban.json
    python -m kanban.board --local  # Generate kanban.json locally only
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WEBSITE_REPO = "mbowdish88/thevalvewire-site"

PROJECTS = {
    "tavr-digest": {
        "owner": "mbowdish88",
        "repo": "tavr-digest",
        "color": "#C4787A",
        "label": "Valve Wire",
    },
    "thevalvewire-site": {
        "owner": "mbowdish88",
        "repo": "thevalvewire-site",
        "color": "#4A90D9",
        "label": "VW Site",
    },
    "baseball-prospect-digest": {
        "owner": "mbowdish88",
        "repo": "baseball-prospect-digest",
        "color": "#50C878",
        "label": "Baseball Digest",
    },
    "pptx-generator": {
        "owner": "mbowdish88",
        "repo": "pptx-generator",
        "color": "#F5A623",
        "label": "PPTX Gen",
    },
    "voice-notes": {
        "owner": "mbowdish88",
        "repo": "voice-notes",
        "color": "#9B59B6",
        "label": "Voice Notes",
    },
    "spotify-curator": {
        "owner": "mbowdish88",
        "repo": "spotify-curator",
        "color": "#1DB954",
        "label": "Spotify",
    },
    "aortic_fl_aats_2022": {
        "owner": "mbowdish88",
        "repo": "aortic_fl_aats_2022",
        "color": "#E74C3C",
        "label": "Aortic FL",
    },
}

KANBAN_LABEL_PREFIX = "kanban:"
KANBAN_COLUMNS = ["backlog", "todo", "in_progress", "review", "done"]
COLUMN_LABELS = {
    "backlog": "Backlog",
    "todo": "To Do",
    "in_progress": "In Progress",
    "review": "Review",
    "done": "Done",
}

LOOKBACK_DAYS = 7


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def _gh_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _gh_get(token: str, url: str, params: dict | None = None) -> list | dict | None:
    try:
        resp = requests.get(url, headers=_gh_headers(token), params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 404:
            return None
        logger.warning("GitHub API %s returned %s: %s", url, resp.status_code, resp.text[:200])
        return None
    except requests.RequestException as e:
        logger.warning("GitHub API request failed: %s", e)
        return None


def _make_card(
    project: str,
    card_type: str,
    title: str,
    url: str,
    author: str,
    timestamp: str,
    status: str = "",
    draggable: bool = False,
    issue_number: int | None = None,
) -> dict:
    card_id = f"{project}/{card_type}/{timestamp}/{title[:30]}"
    return {
        "id": card_id,
        "project": project,
        "type": card_type,
        "title": title,
        "url": url,
        "author": author,
        "timestamp": timestamp,
        "status": status,
        "draggable": draggable,
        "issue_number": issue_number,
    }


# ---------------------------------------------------------------------------
# Data fetchers (per repo)
# ---------------------------------------------------------------------------

def _fetch_commits(token: str, owner: str, repo: str, since: str) -> list[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    data = _gh_get(token, url, {"since": since, "per_page": 20})
    if not data or not isinstance(data, list):
        return []
    cards = []
    for c in data:
        commit = c.get("commit", {})
        author = c.get("author", {}).get("login", commit.get("author", {}).get("name", "unknown"))
        msg = commit.get("message", "").split("\n")[0][:80]
        cards.append(_make_card(
            project=repo,
            card_type="commit",
            title=msg,
            url=c.get("html_url", ""),
            author=author,
            timestamp=commit.get("author", {}).get("date", ""),
            status="committed",
        ))
    return cards


def _fetch_prs(token: str, owner: str, repo: str) -> list[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    data = _gh_get(token, url, {"state": "all", "per_page": 20, "sort": "updated", "direction": "desc"})
    if not data or not isinstance(data, list):
        return []
    cards = []
    for pr in data:
        status = pr.get("state", "open")
        if pr.get("merged_at"):
            status = "merged"
        elif pr.get("draft"):
            status = "draft"
        cards.append(_make_card(
            project=repo,
            card_type="pr",
            title=pr.get("title", ""),
            url=pr.get("html_url", ""),
            author=pr.get("user", {}).get("login", "unknown"),
            timestamp=pr.get("updated_at", ""),
            status=status,
        ))
    return cards


def _fetch_issues(token: str, owner: str, repo: str) -> list[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    data = _gh_get(token, url, {"state": "all", "per_page": 30, "sort": "updated", "direction": "desc"})
    if not data or not isinstance(data, list):
        return []
    cards = []
    for issue in data:
        if issue.get("pull_request"):
            continue  # Skip PRs (GitHub API returns them as issues too)
        labels = [l.get("name", "") for l in issue.get("labels", [])]
        is_kanban = any(l.startswith(KANBAN_LABEL_PREFIX) or l == "kanban" for l in labels)
        cards.append(_make_card(
            project=repo,
            card_type="custom" if is_kanban else "issue",
            title=issue.get("title", ""),
            url=issue.get("html_url", ""),
            author=issue.get("user", {}).get("login", "unknown"),
            timestamp=issue.get("updated_at", ""),
            status=issue.get("state", "open"),
            draggable=is_kanban,
            issue_number=issue.get("number"),
        ))
    return cards


def _fetch_workflows(token: str, owner: str, repo: str) -> list[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    data = _gh_get(token, url, {"per_page": 10})
    if not data or not isinstance(data, dict):
        return []
    cards = []
    for run in data.get("workflow_runs", []):
        conclusion = run.get("conclusion") or run.get("status", "pending")
        cards.append(_make_card(
            project=repo,
            card_type="workflow",
            title=f"{run.get('name', 'Workflow')} #{run.get('run_number', '')}",
            url=run.get("html_url", ""),
            author=run.get("actor", {}).get("login", "unknown"),
            timestamp=run.get("updated_at", ""),
            status=conclusion,
        ))
    return cards


# ---------------------------------------------------------------------------
# Column assignment logic
# ---------------------------------------------------------------------------

def _get_kanban_column(labels: list[str]) -> str | None:
    """Extract kanban column from issue labels."""
    for label in labels:
        if label.startswith(KANBAN_LABEL_PREFIX):
            col = label[len(KANBAN_LABEL_PREFIX):]
            col_normalized = col.lower().replace(" ", "_").replace("-", "_")
            if col_normalized in KANBAN_COLUMNS:
                return col_normalized
    return None


def _assign_column(card: dict, issue_labels: list[str] | None = None) -> str:
    """Assign a card to a kanban column based on type and status."""
    # Custom tasks: use their kanban label
    if card["type"] == "custom" and issue_labels:
        col = _get_kanban_column(issue_labels)
        if col:
            return col
        return "backlog"

    # PRs
    if card["type"] == "pr":
        if card["status"] == "merged":
            return "done"
        if card["status"] == "draft":
            return "in_progress"
        if card["status"] == "open":
            return "review"
        if card["status"] == "closed":
            return "done"

    # Workflow runs
    if card["type"] == "workflow":
        if card["status"] in ("success", "completed"):
            return "done"
        if card["status"] in ("failure", "action_required"):
            return "in_progress"
        if card["status"] in ("in_progress", "queued", "pending"):
            return "in_progress"
        return "done"

    # Issues (non-kanban)
    if card["type"] == "issue":
        if card["status"] == "open":
            return "backlog"
        return "done"

    # Commits
    if card["type"] == "commit":
        return "done"

    return "backlog"


# ---------------------------------------------------------------------------
# Main data builder
# ---------------------------------------------------------------------------

def build_kanban_data(token: str) -> dict:
    """Build the full kanban board JSON structure."""
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=LOOKBACK_DAYS)).isoformat()

    columns = {col: {"label": COLUMN_LABELS[col], "cards": []} for col in KANBAN_COLUMNS}

    projects_meta = {}
    for repo_name, info in PROJECTS.items():
        projects_meta[repo_name] = {
            "color": info["color"],
            "label": info["label"],
            "url": f"https://github.com/{info['owner']}/{info['repo']}",
        }

        owner, repo = info["owner"], info["repo"]
        logger.info("Fetching data for %s/%s...", owner, repo)

        # Fetch all data types
        commits = _fetch_commits(token, owner, repo, since)
        prs = _fetch_prs(token, owner, repo)
        issues = _fetch_issues(token, owner, repo)
        workflows = _fetch_workflows(token, owner, repo)

        # Build a lookup of issue labels by issue number
        issue_labels_map = {}
        for issue_data in (_gh_get(token, f"https://api.github.com/repos/{owner}/{repo}/issues",
                                   {"state": "all", "per_page": 30}) or []):
            if isinstance(issue_data, dict):
                num = issue_data.get("number")
                labels = [l.get("name", "") for l in issue_data.get("labels", [])]
                issue_labels_map[num] = labels

        # Assign cards to columns
        all_cards = commits + prs + issues + workflows
        for card in all_cards:
            labels = issue_labels_map.get(card.get("issue_number")) if card.get("issue_number") else None
            col = _assign_column(card, labels)
            columns[col]["cards"].append(card)

    # Sort cards within each column by timestamp (newest first)
    for col in columns.values():
        col["cards"].sort(key=lambda c: c.get("timestamp", ""), reverse=True)

    # Limit cards per column to keep payload reasonable
    MAX_CARDS_PER_COLUMN = 50
    for col in columns.values():
        col["cards"] = col["cards"][:MAX_CARDS_PER_COLUMN]

    return {
        "updated_at": now.isoformat(),
        "projects": projects_meta,
        "columns": columns,
    }


# ---------------------------------------------------------------------------
# Push to website repo
# ---------------------------------------------------------------------------

def _github_api_put_file(token: str, path: str, content: str, message: str) -> bool:
    """Create or update a file in the website repo via GitHub API."""
    url = f"https://api.github.com/repos/{WEBSITE_REPO}/contents/{path}"
    headers = _gh_headers(token)

    sha = None
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        sha = resp.json().get("sha")

    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "committer": {"name": "valve-wire-bot", "email": "bot@thevalvewire.com"},
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, json=payload, timeout=30)
    if resp.status_code in (200, 201):
        return True
    logger.error("GitHub API put failed for %s: %s %s", path, resp.status_code, resp.text[:200])
    return False


def push_kanban(data: dict, html_content: str | None = None) -> bool:
    """Push kanban.json (and optionally the HTML board) to the website repo."""
    token = os.getenv("WEBSITE_GITHUB_TOKEN", os.getenv("GITHUB_TOKEN", ""))
    if not token:
        logger.warning("No GITHUB_TOKEN, skipping kanban push")
        return False

    json_content = json.dumps(data, indent=2, default=str)

    ok1 = _github_api_put_file(
        token, "public/data/kanban.json", json_content,
        f"Update kanban board {data['updated_at'][:10]}",
    )

    ok2 = True
    if html_content:
        ok2 = _github_api_put_file(
            token, "public/kanban/index.html", html_content,
            "Update kanban board page",
        )

    if ok1:
        logger.info("Kanban JSON pushed successfully")
    if html_content and ok2:
        logger.info("Kanban HTML pushed successfully")

    return ok1 and ok2


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate kanban board data")
    parser.add_argument("--local", action="store_true", help="Write JSON locally instead of pushing")
    parser.add_argument("--push-html", action="store_true", help="Also push the HTML board page")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    token = os.getenv("WEBSITE_GITHUB_TOKEN", os.getenv("GITHUB_TOKEN", ""))
    if not token:
        logger.error("Set GITHUB_TOKEN or WEBSITE_GITHUB_TOKEN environment variable")
        sys.exit(1)

    logger.info("Building kanban data for %d projects...", len(PROJECTS))
    data = build_kanban_data(token)

    total_cards = sum(len(col["cards"]) for col in data["columns"].values())
    logger.info("Generated %d cards across %d columns", total_cards, len(data["columns"]))

    if args.local:
        out_path = Path(__file__).parent / "kanban.json"
        out_path.write_text(json.dumps(data, indent=2, default=str))
        logger.info("Written to %s", out_path)
    else:
        html_content = None
        if args.push_html:
            html_path = Path(__file__).parent / "board.html"
            if html_path.exists():
                html_content = html_path.read_text()
            else:
                logger.warning("board.html not found, skipping HTML push")

        push_kanban(data, html_content)


if __name__ == "__main__":
    main()
