"""Always-on conversational Telegram bot powered by Claude.

Runs as a long-polling loop on Railway. Handles both slash commands
and natural language via Claude API.
"""

from __future__ import annotations

import io
import json
import logging
import os
import time
import zipfile
from datetime import datetime, timezone

import requests
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("valve-wire-bot")

# --- Config ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
REPO = "mbowdish88/tavr-digest"

WORKFLOWS = {
    "daily": "daily-digest.yml",
    "weekly": "weekly-digest.yml",
    "podcast": "weekly-podcast.yml",
}

SYSTEM_PROMPT = """\
You are the Valve Wire Monitor — an AI assistant that manages "The Valve Wire", \
a daily medical newsletter and weekly podcast about transcatheter valve technology.

You communicate via Telegram with the project owner (Michael). Be concise — this is \
a chat interface, not an essay. Use short messages, emoji where appropriate.

You have access to these tools via function results that will be provided to you:

PIPELINE STATUS: You can check the status of GitHub Actions workflows (daily digest, \
weekly digest, podcast). Each runs automatically — daily at 6 AM CT, weekly on Saturday.

WORKFLOW LOGS: You can pull error logs from any workflow run.

RERUN WORKFLOWS: You can trigger a rerun of any failed workflow.

GITHUB INFO: You can check open PRs, recent commits, and repo status.

WEBSITE: The site is at thevalvewire.com (GitHub Pages). It updates automatically.

When Michael asks you something:
- If it's about pipeline status, check the workflows
- If it's about errors, pull the logs
- If it's a request to fix or rerun something, do it
- If it's a general question about the project, answer from your knowledge
- If you're not sure, ask for clarification
- Keep responses short and actionable

The pipeline: Sources (PubMed, journals, news, FDA, trials, stocks) -> Dedup -> \
Claude summarization -> Email delivery + GitHub Pages website. Weekly also generates \
a podcast via OpenAI TTS.

Current known issues: None critical. All systems operational as of last check."""

# --- GitHub API helpers ---
def github_api(endpoint: str, method: str = "GET", data: dict = None) -> dict | None:
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com{endpoint}"
    try:
        if method == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=15)
        else:
            resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code in (200, 201, 204):
            return resp.json() if resp.content else {}
        logger.warning(f"GitHub API {resp.status_code}: {endpoint}")
        return None
    except Exception as e:
        logger.error(f"GitHub API error: {e}")
        return None


def get_pipeline_status() -> str:
    """Get status of all workflows."""
    lines = []
    for name, filename in WORKFLOWS.items():
        data = github_api(f"/repos/{REPO}/actions/workflows/{filename}/runs?per_page=1")
        if data and data.get("workflow_runs"):
            run = data["workflow_runs"][0]
            status = run["conclusion"] or run["status"]
            icon = "✅" if status == "success" else "❌" if status == "failure" else "⏳"
            created = run["created_at"][:16].replace("T", " ")
            lines.append(f"{icon} {name}: {status} - {created}")
        else:
            lines.append(f"? {name}: no data")
    return "\n".join(lines)


def get_workflow_errors(workflow: str = "daily") -> str:
    """Get errors from the most recent run."""
    filename = WORKFLOWS.get(workflow)
    if not filename:
        return f"Unknown workflow: {workflow}. Try: daily, weekly, podcast"

    data = github_api(f"/repos/{REPO}/actions/workflows/{filename}/runs?per_page=1")
    if not data or not data.get("workflow_runs"):
        return "No runs found."

    run = data["workflow_runs"][0]
    run_id = run["id"]
    conclusion = run["conclusion"] or run["status"]

    # Download logs
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/logs",
            headers=headers, timeout=30, allow_redirects=True,
        )
        if resp.status_code != 200:
            return f"Could not fetch logs (HTTP {resp.status_code})"

        errors = []
        warnings = []
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for name in zf.namelist():
                content = zf.read(name).decode("utf-8", errors="replace")
                for line in content.split("\n"):
                    if "[ERROR]" in line:
                        parts = line.split("[ERROR]", 1)
                        errors.append(parts[1].strip()[:150] if len(parts) > 1 else line[:150])
                    elif "[WARNING]" in line:
                        parts = line.split("[WARNING]", 1)
                        warnings.append(parts[1].strip()[:150] if len(parts) > 1 else line[:150])

        lines = [f"Logs: {workflow} ({conclusion})"]
        if errors:
            lines.append(f"\nErrors ({len(errors)}):")
            for e in errors[:8]:
                lines.append(f"  x {e}")
        if warnings:
            lines.append(f"\nWarnings ({len(warnings)}):")
            for w in warnings[:5]:
                lines.append(f"  ! {w}")
        if not errors and not warnings:
            lines.append("No errors or warnings.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading logs: {e}"


def rerun_workflow(workflow: str = "") -> str:
    """Rerun a workflow."""
    if not workflow:
        # Find most recent failed
        for name, filename in WORKFLOWS.items():
            data = github_api(f"/repos/{REPO}/actions/workflows/{filename}/runs?per_page=1")
            if data and data.get("workflow_runs"):
                run = data["workflow_runs"][0]
                if run["conclusion"] == "failure":
                    workflow = name
                    break
        if not workflow:
            return "No failed workflows to rerun."

    filename = WORKFLOWS.get(workflow)
    if not filename:
        return f"Unknown workflow: {workflow}"

    result = github_api(f"/repos/{REPO}/actions/workflows/{filename}/dispatches", "POST", {"ref": "main"})
    if result is not None:
        return f"🔄 Triggered {workflow} run"
    return f"Failed to trigger {workflow}"


def get_open_prs() -> str:
    """Get open PRs."""
    data = github_api(f"/repos/{REPO}/pulls?state=open")
    if not data:
        return "Could not fetch PRs."
    if not data:
        return "No open PRs."
    lines = [f"Open PRs: {len(data)}"]
    for pr in data[:5]:
        lines.append(f"  - {pr['title']}: {pr['html_url']}")
    return "\n".join(lines)


def check_website() -> str:
    """Check if thevalvewire.com is up."""
    try:
        resp = requests.get("https://thevalvewire.com", timeout=10)
        return f"🌐 Website: {'online' if resp.status_code == 200 else f'HTTP {resp.status_code}'}"
    except Exception:
        return "🌐 Website: unreachable"


# --- Claude conversation ---
def get_context() -> str:
    """Build current context for Claude."""
    status = get_pipeline_status()
    website = check_website()
    return f"Current pipeline status:\n{status}\n\n{website}"


def ask_claude(message: str, context: str) -> str:
    """Send a message to Claude with pipeline context."""
    if not ANTHROPIC_API_KEY:
        return "Claude API not configured."

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    user_content = f"Context:\n{context}\n\nUser message: {message}"

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Claude error: {e}")
        return f"Claude error: {e}"


# --- Telegram ---
def send_message(text: str):
    """Send a message via Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # Telegram has a 4096 char limit
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (truncated)"
    try:
        resp = requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Telegram send failed: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"Telegram error: {e}")


def process_message(text: str):
    """Process an incoming message — slash command or natural language."""
    text = text.strip()

    # Slash commands (fast path, no Claude needed)
    if text.startswith("/"):
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "/status":
            status = get_pipeline_status()
            website = check_website()
            send_message(f"Pipeline Status\n\n{status}\n\n{website}")
        elif cmd == "/logs":
            send_message(get_workflow_errors(args or "daily"))
        elif cmd == "/rerun":
            send_message(rerun_workflow(args))
        elif cmd == "/fix":
            send_message(get_open_prs())
        elif cmd == "/cost":
            send_message("Cost tracking coming soon. Current estimate: ~165 min/month of 2,000 free GitHub Actions minutes.")
        elif cmd in ("/help", "/start"):
            send_message(
                "Valve Wire Monitor\n\n"
                "Commands:\n"
                "/status - Pipeline status\n"
                "/logs - Errors from last run\n"
                "/logs weekly - Errors from specific workflow\n"
                "/rerun - Rerun failed workflow\n"
                "/rerun daily - Rerun specific\n"
                "/fix - Open PRs\n"
                "/help - This message\n\n"
                "Or just ask me anything about the pipeline in plain English."
            )
        else:
            send_message(f"Unknown command: {cmd}\nTry /help or just ask me a question.")
        return

    # Natural language — send to Claude
    context = get_context()

    # Check if the message implies an action
    lower = text.lower()
    if any(word in lower for word in ["rerun", "retry", "run again", "trigger"]):
        # Figure out which workflow
        for name in WORKFLOWS:
            if name in lower:
                result = rerun_workflow(name)
                send_message(result)
                return
        # Ask Claude to figure it out
        pass

    if any(word in lower for word in ["error", "log", "what happened", "what went wrong", "fail"]):
        for name in WORKFLOWS:
            if name in lower:
                errors = get_workflow_errors(name)
                send_message(errors)
                return
        # Default to daily
        errors = get_workflow_errors("daily")
        context += f"\n\nLatest daily log errors:\n{errors}"

    response = ask_claude(text, context)
    send_message(response)


# --- Main loop ---
def main():
    logger.info("Valve Wire Bot starting...")

    if not BOT_TOKEN or not CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID required")
        return

    send_message("🟢 Valve Wire Monitor is online.")

    offset = 0
    consecutive_errors = 0

    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"timeout": 30, "offset": offset}
            resp = requests.get(url, params=params, timeout=35)

            if resp.status_code != 200:
                logger.error(f"getUpdates failed: {resp.status_code}")
                consecutive_errors += 1
                time.sleep(min(30 * consecutive_errors, 300))
                continue

            consecutive_errors = 0
            updates = resp.json().get("result", [])

            for update in updates:
                offset = update["update_id"] + 1
                message = update.get("message", {})
                text = message.get("text", "")
                from_id = str(message.get("chat", {}).get("id", ""))

                if from_id != CHAT_ID:
                    logger.warning(f"Ignoring message from {from_id}")
                    continue

                if text:
                    logger.info(f"Message: {text}")
                    try:
                        process_message(text)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        send_message(f"Error: {e}")

        except requests.exceptions.Timeout:
            continue  # Normal for long polling
        except Exception as e:
            logger.error(f"Poll error: {e}")
            consecutive_errors += 1
            time.sleep(min(10 * consecutive_errors, 120))


if __name__ == "__main__":
    main()
