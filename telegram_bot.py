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
    try:
        resp = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        }, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Telegram send failed: {resp.status_code} {resp.text}")
            # Retry without Markdown in case of formatting issues
            resp2 = requests.post(url, json={
                "chat_id": CHAT_ID,
                "text": text,
            }, timeout=10)
            if resp2.status_code != 200:
                logger.error(f"Telegram retry also failed: {resp2.status_code}")
        else:
            logger.info("Telegram message sent")
    except Exception as e:
        logger.error(f"Telegram send error: {e}")


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
    lines = ["Pipeline Status\n"]

    for name, filename in WORKFLOWS.items():
        url = f"https://api.github.com/repos/{REPO}/actions/workflows/{filename}/runs?per_page=1"
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            logger.info(f"GitHub API {name}: HTTP {resp.status_code}")
            if resp.status_code == 200:
                runs = resp.json().get("workflow_runs", [])
                if runs:
                    run = runs[0]
                    status = run["conclusion"] or run["status"]
                    icon = "✅" if status == "success" else "❌" if status == "failure" else "⏳"
                    created = run["created_at"][:16].replace("T", " ")
                    lines.append(f"{icon} {name}: {status} - {created}")
                else:
                    lines.append(f"? {name}: no runs found")
            else:
                lines.append(f"? {name}: API error {resp.status_code}")
        except Exception as e:
            logger.error(f"Status check failed for {name}: {e}")
            lines.append(f"? {name}: {e}")

    # Open auto-fix PRs
    try:
        pr_resp = requests.get(
            f"https://api.github.com/repos/{REPO}/pulls?state=open",
            headers=headers, timeout=10,
        )
        if pr_resp.status_code == 200:
            prs = [p for p in pr_resp.json() if p["head"]["ref"].startswith("fix/")]
            if prs:
                lines.append(f"\nOpen fix PRs: {len(prs)}")
                for pr in prs[:3]:
                    lines.append(f"  - {pr['title']}: {pr['html_url']}")
    except Exception:
        pass

    msg = "\n".join(lines)
    logger.info(f"Status message: {msg}")
    send_message(msg)


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


def cmd_logs(args: str = ""):
    """Show errors from the most recent run of a workflow."""
    target = args.strip().lower() if args else "daily"
    if target not in WORKFLOWS:
        send_message(f"Unknown workflow: {target}\nTry: /logs daily, /logs weekly, /logs podcast")
        return

    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    filename = WORKFLOWS[target]

    # Get latest run
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{filename}/runs?per_page=1"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            send_message(f"API error: {resp.status_code}")
            return
        runs = resp.json().get("workflow_runs", [])
        if not runs:
            send_message(f"No runs found for {target}")
            return
        run = runs[0]
        run_id = run["id"]
        conclusion = run["conclusion"] or run["status"]
    except Exception as e:
        send_message(f"Error: {e}")
        return

    # Download logs
    log_url = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/logs"
    try:
        import io
        import zipfile
        resp = requests.get(log_url, headers=headers, timeout=30, allow_redirects=True)
        if resp.status_code != 200:
            send_message(f"Could not fetch logs: HTTP {resp.status_code}")
            return

        errors = []
        warnings = []
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for name in zf.namelist():
                content = zf.read(name).decode("utf-8", errors="replace")
                for line in content.split("\n"):
                    if "[ERROR]" in line:
                        # Extract just the message part
                        parts = line.split("[ERROR]", 1)
                        errors.append(parts[1].strip()[:150] if len(parts) > 1 else line[:150])
                    elif "[WARNING]" in line:
                        parts = line.split("[WARNING]", 1)
                        warnings.append(parts[1].strip()[:150] if len(parts) > 1 else line[:150])

        lines = [f"Logs: {target} ({conclusion})\n"]
        if errors:
            lines.append(f"Errors ({len(errors)}):")
            for e in errors[:8]:
                lines.append(f"  x {e}")
        if warnings:
            lines.append(f"\nWarnings ({len(warnings)}):")
            for w in warnings[:5]:
                lines.append(f"  ! {w}")
        if not errors and not warnings:
            lines.append("No errors or warnings found.")

        send_message("\n".join(lines))
    except Exception as e:
        send_message(f"Error reading logs: {e}")


def cmd_cost():
    """Show GitHub Actions minutes usage this month."""
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}

    # Get billing info
    try:
        # Get recent runs to estimate usage
        lines = ["Actions Usage (last 7 days)\n"]
        total_minutes = 0

        for name, filename in WORKFLOWS.items():
            url = f"https://api.github.com/repos/{REPO}/actions/workflows/{filename}/runs?per_page=10"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                runs = resp.json().get("workflow_runs", [])
                workflow_mins = 0
                count = 0
                for run in runs:
                    if run.get("run_started_at") and run.get("updated_at"):
                        from datetime import datetime
                        start = datetime.fromisoformat(run["run_started_at"].replace("Z", "+00:00"))
                        end = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                        mins = (end - start).total_seconds() / 60
                        workflow_mins += mins
                        count += 1
                total_minutes += workflow_mins
                lines.append(f"{name}: {count} runs, ~{workflow_mins:.0f} min")

        # Add monitor + telegram polling estimate
        lines.append(f"monitor: triggers after each run")
        lines.append(f"telegram: ~32 polls/day")
        lines.append(f"\nEstimated total: ~{total_minutes:.0f} min")
        lines.append(f"Free tier: 2,000 min/month")

        send_message("\n".join(lines))
    except Exception as e:
        send_message(f"Error: {e}")


def cmd_help():
    """Show available commands."""
    send_message(
        "Valve Wire Monitor Commands\n\n"
        "/status - Pipeline status\n"
        "/logs - Errors from last daily run\n"
        "/logs daily|weekly|podcast - Errors from specific workflow\n"
        "/cost - GitHub Actions usage\n"
        "/rerun - Rerun failed workflow\n"
        "/rerun daily|weekly|podcast - Rerun specific\n"
        "/fix - Open auto-fix PRs\n"
        "/help - Show this message"
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
        "/logs": lambda: cmd_logs(args),
        "/cost": lambda: cmd_cost(),
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
