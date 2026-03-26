"""Telegram bot for two-way commands — polls for messages and responds."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("telegram-bot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO = os.getenv("GITHUB_REPO", "mbowdish88/tavr-digest")
OFFSET_FILE = Path(".telegram_offset")

WORKFLOWS = {
    "daily": "daily-digest.yml",
    "weekly": "weekly-digest.yml",
    "podcast": "weekly-podcast.yml",
}


def send_message(text: str):
    """Send a message to the user."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }, timeout=10)


def get_updates(offset: int = 0) -> list:
    """Get new messages from Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 5}
    if offset:
        params["offset"] = offset

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("result", [])
    except Exception as e:
        logger.error(f"getUpdates failed: {e}")
    return []


def load_offset() -> int:
    """Load the last processed update ID."""
    if OFFSET_FILE.exists():
        try:
            return int(OFFSET_FILE.read_text().strip())
        except ValueError:
            pass
    return 0


def save_offset(offset: int):
    """Save the last processed update ID."""
    OFFSET_FILE.write_text(str(offset))


def cmd_status():
    """Get status of all workflows."""
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    lines = ["*Pipeline Status*\n"]

    for name, filename in WORKFLOWS.items():
        url = f"https://api.github.com/repos/{REPO}/actions/workflows/{filename}/runs?per_page=1"
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                runs = resp.json().get("workflow_runs", [])
                if runs:
                    run = runs[0]
                    status = run["conclusion"] or run["status"]
                    icon = "✅" if status == "success" else "❌" if status == "failure" else "⏳"
                    created = run["created_at"][:16].replace("T", " ")
                    duration = ""
                    if run.get("run_started_at") and run["conclusion"]:
                        # Approximate duration from the run
                        duration = f" ({run.get('conclusion', '')})"
                    lines.append(f"{icon} *{name}*: {status} — {created}")
                else:
                    lines.append(f"❓ *{name}*: no runs found")
            else:
                lines.append(f"❓ *{name}*: API error {resp.status_code}")
        except Exception as e:
            lines.append(f"❓ *{name}*: {e}")

    # Open auto-fix PRs
    try:
        pr_resp = requests.get(
            f"https://api.github.com/repos/{REPO}/pulls?state=open&head=fix/",
            headers=headers, timeout=10,
        )
        if pr_resp.status_code == 200:
            prs = [p for p in pr_resp.json() if p["head"]["ref"].startswith("fix/")]
            if prs:
                lines.append(f"\n🔧 *Open fix PRs:* {len(prs)}")
                for pr in prs[:3]:
                    lines.append(f"  • [{pr['title']}]({pr['html_url']})")
    except Exception:
        pass

    send_message("\n".join(lines))


def cmd_rerun(args: str = ""):
    """Rerun the most recent failed workflow."""
    target = args.strip().lower() if args else None
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}

    # Find the most recent failed run
    candidates = []
    for name, filename in WORKFLOWS.items():
        if target and target != name:
            continue
        url = f"https://api.github.com/repos/{REPO}/actions/workflows/{filename}/runs?per_page=1"
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                runs = resp.json().get("workflow_runs", [])
                if runs:
                    run = runs[0]
                    if run["conclusion"] == "failure" or target:
                        candidates.append((name, run))
        except Exception:
            pass

    if not candidates:
        send_message("✅ No failed workflows to rerun." + (" Try `/rerun daily`, `/rerun weekly`, or `/rerun podcast`." if not target else ""))
        return

    name, run = candidates[0]
    rerun_url = f"https://api.github.com/repos/{REPO}/actions/runs/{run['id']}/rerun"
    try:
        resp = requests.post(rerun_url, headers=headers, timeout=10)
        if resp.status_code == 201:
            send_message(f"🔄 Rerunning *{name}* (run {run['id']})")
        else:
            # Try triggering a fresh run instead
            dispatch_url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOWS[name]}/dispatches"
            resp2 = requests.post(dispatch_url, headers=headers, json={"ref": "main"}, timeout=10)
            if resp2.status_code == 204:
                send_message(f"🔄 Triggered fresh *{name}* run")
            else:
                send_message(f"❌ Failed to rerun *{name}*: HTTP {resp.status_code}")
    except Exception as e:
        send_message(f"❌ Rerun failed: {e}")


def cmd_fix():
    """List open auto-fix PRs."""
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}

    try:
        resp = requests.get(
            f"https://api.github.com/repos/{REPO}/pulls?state=open",
            headers=headers, timeout=10,
        )
        if resp.status_code == 200:
            prs = [p for p in resp.json() if p["head"]["ref"].startswith("fix/")]
            if prs:
                lines = ["🔧 *Open auto-fix PRs:*\n"]
                for pr in prs:
                    lines.append(f"• [{pr['title']}]({pr['html_url']})")
                    lines.append(f"  _{pr['body'][:100]}..._\n")
                send_message("\n".join(lines))
            else:
                send_message("✅ No open auto-fix PRs.")
        else:
            send_message(f"❌ API error: {resp.status_code}")
    except Exception as e:
        send_message(f"❌ Error: {e}")


def cmd_help():
    """Show available commands."""
    send_message(
        "*Valve Wire Monitor Commands*\n\n"
        "/status — Show pipeline status\n"
        "/rerun — Rerun failed workflow\n"
        "/rerun daily|weekly|podcast — Rerun specific workflow\n"
        "/fix — Show open auto-fix PRs\n"
        "/help — Show this message"
    )


def process_message(text: str):
    """Route a command to the right handler."""
    text = text.strip()
    if not text.startswith("/"):
        return

    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    handlers = {
        "/status": lambda: cmd_status(),
        "/rerun": lambda: cmd_rerun(args),
        "/fix": lambda: cmd_fix(),
        "/help": lambda: cmd_help(),
        "/start": lambda: cmd_help(),
    }

    handler = handlers.get(cmd)
    if handler:
        handler()
    else:
        send_message(f"Unknown command: `{cmd}`\nTry /help")


def main():
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("Telegram credentials not configured")
        return

    offset = load_offset()
    updates = get_updates(offset)

    if not updates:
        logger.info("No new messages")
        return

    for update in updates:
        update_id = update["update_id"]
        message = update.get("message", {})
        text = message.get("text", "")
        from_id = str(message.get("chat", {}).get("id", ""))

        # Only respond to our authorized user
        if from_id != CHAT_ID:
            logger.warning(f"Ignoring message from unauthorized chat: {from_id}")
            continue

        if text:
            logger.info(f"Processing command: {text}")
            process_message(text)

        offset = update_id + 1

    save_offset(offset)
    logger.info(f"Processed {len(updates)} updates, new offset: {offset}")


if __name__ == "__main__":
    main()
