"""Send a daily morning summary via Telegram."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("daily-summary")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO = "mbowdish88/tavr-digest"

WORKFLOWS = {
    "daily": "daily-digest.yml",
    "weekly": "weekly-digest.yml",
    "podcast": "weekly-podcast.yml",
    "monitor": "monitor.yml",
    "telegram": "telegram-commands.yml",
}


def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Telegram send failed: {resp.status_code}")
        else:
            logger.info("Summary sent")
    except Exception as e:
        logger.error(f"Telegram error: {e}")


def get_recent_runs(filename: str, count: int = 1) -> list:
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{filename}/runs?per_page={count}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("workflow_runs", [])
    except Exception:
        pass
    return []


def main():
    now = datetime.now(timezone.utc)
    today = now.strftime("%A, %B %d")

    lines = [f"Good morning! Here's your Valve Wire summary for {today}.\n"]

    # Check each workflow
    all_ok = True
    for name, filename in WORKFLOWS.items():
        if name in ("monitor", "telegram"):
            continue  # Skip infrastructure workflows

        runs = get_recent_runs(filename, 1)
        if runs:
            run = runs[0]
            conclusion = run["conclusion"] or run["status"]
            created = run["created_at"][:16].replace("T", " ")
            icon = "✅" if conclusion == "success" else "❌" if conclusion == "failure" else "⏳"
            lines.append(f"{icon} {name}: {conclusion} - {created}")

            if conclusion == "failure":
                all_ok = False

            # Extract article count from daily run name/logs
            if name == "daily" and conclusion == "success":
                # Check if the run committed new content
                pass
        else:
            lines.append(f"? {name}: no recent runs")

    # Website status
    try:
        resp = requests.get("https://thevalvewire.com", timeout=10)
        if resp.status_code == 200:
            lines.append(f"\n🌐 Website: online")
        else:
            lines.append(f"\n🌐 Website: HTTP {resp.status_code}")
            all_ok = False
    except Exception:
        lines.append(f"\n🌐 Website: unreachable")
        all_ok = False

    # Open PRs
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    try:
        resp = requests.get(f"https://api.github.com/repos/{REPO}/pulls?state=open", headers=headers, timeout=10)
        if resp.status_code == 200:
            prs = resp.json()
            if prs:
                lines.append(f"\nOpen PRs: {len(prs)}")
                for pr in prs[:3]:
                    lines.append(f"  - {pr['title']}")
    except Exception:
        pass

    if all_ok:
        lines.append("\nAll systems operational. Have a great day!")
    else:
        lines.append("\n⚠️ Issues detected — check /status or /logs for details.")

    send_telegram("\n".join(lines))


if __name__ == "__main__":
    main()
