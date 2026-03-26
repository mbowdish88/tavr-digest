"""Pipeline monitoring agent — analyzes workflow logs, fixes bugs, sends alerts."""

from __future__ import annotations

import io
import json
import logging
import os
import smtplib
import subprocess
import zipfile
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("monitor")

# --- Config from environment ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
WORKFLOW_RUN_ID = os.getenv("WORKFLOW_RUN_ID", "")
WORKFLOW_NAME = os.getenv("WORKFLOW_NAME", "")
WORKFLOW_CONCLUSION = os.getenv("WORKFLOW_CONCLUSION", "")
REPO = "mbowdish88/tavr-digest"

ANALYSIS_PROMPT = """\
You are a CI/CD monitoring agent for "The Valve Wire", a medical newsletter automation pipeline.

Analyze these GitHub Actions workflow logs and return a JSON response with this exact schema:
{
  "severity": "OK" | "WARNING" | "ERROR" | "CRITICAL",
  "summary": "One-line human-readable summary",
  "details": "2-3 sentence explanation of what happened",
  "errors": ["list of error descriptions"],
  "warnings": ["list of warning descriptions"],
  "root_cause": "If failed, describe the root cause",
  "is_code_bug": true or false,
  "fix": {
    "file": "path/to/file.py",
    "description": "What the fix does",
    "old_code": "exact code to replace",
    "new_code": "replacement code"
  } or null,
  "metrics": {
    "articles_processed": number or null,
    "articles_new": number or null,
    "email_sent": true or false or null,
    "duration_seconds": number or null
  }
}

Context: The pipeline fetches medical articles from PubMed, preprints, journals, news, FDA, \
clinical trials, stock data, then uses Claude to generate a newsletter HTML, and delivers via \
email and GitHub Pages website. Weekly also generates a podcast via OpenAI TTS.

Common failure modes:
- API rate limits or timeouts (PubMed, bioRxiv, Yahoo Finance, Claude, OpenAI)
- SMTP authentication failures (Gmail app password)
- Python type errors from API response changes
- Dictionary mutation during iteration
- Missing data causing empty responses

Classify severity:
- OK: Everything worked, no errors
- WARNING: Completed but with non-critical errors (e.g., one source timed out)
- ERROR: Key functionality failed (email not sent, no articles found)
- CRITICAL: Complete pipeline failure

Only set is_code_bug=true if you are confident the fix is correct and targeted.
Only propose fixes for Python files, not YAML workflows.
Keep fixes under 20 lines changed.

Return ONLY the JSON, no markdown formatting."""


def fetch_workflow_logs(run_id: str) -> str:
    """Download and extract workflow logs from GitHub API."""
    url = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/logs"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}

    resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
    if resp.status_code != 200:
        logger.error(f"Failed to fetch logs: HTTP {resp.status_code}")
        return ""

    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            logs = []
            for name in zf.namelist():
                # Prioritize the main run step, skip setup/cleanup
                content = zf.read(name).decode("utf-8", errors="replace")
                logs.append(f"=== {name} ===\n{content}")
            full_log = "\n".join(logs)
    except zipfile.BadZipFile:
        logger.error("Invalid ZIP file from GitHub API")
        return ""

    # Truncate to ~100K chars for Claude context
    if len(full_log) > 100000:
        full_log = full_log[:50000] + "\n\n... [TRUNCATED] ...\n\n" + full_log[-50000:]

    logger.info(f"Fetched logs: {len(full_log)} chars from run {run_id}")
    return full_log


def analyze_logs(logs: str, workflow_name: str, conclusion: str) -> dict:
    """Send logs to Claude for analysis."""
    if not ANTHROPIC_API_KEY:
        logger.error("No Anthropic API key configured")
        return {"severity": "ERROR", "summary": "Monitor misconfigured: no API key"}

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    user_prompt = (
        f"Workflow: {workflow_name}\n"
        f"Conclusion: {conclusion}\n"
        f"Timestamp: {datetime.utcnow().isoformat()}Z\n\n"
        f"--- LOGS ---\n{logs}"
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=ANALYSIS_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        result = json.loads(message.content[0].text)
        logger.info(f"Analysis: {result.get('severity')} — {result.get('summary')}")
        return result
    except json.JSONDecodeError:
        logger.error("Claude returned non-JSON response")
        return {"severity": "WARNING", "summary": "Monitor could not parse Claude response"}
    except Exception as e:
        logger.error(f"Claude analysis failed: {e}")
        return {"severity": "ERROR", "summary": f"Monitor analysis failed: {e}"}


def send_telegram(message: str) -> bool:
    """Send a message via Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured, skipping")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("Telegram notification sent")
            return True
        else:
            logger.error(f"Telegram send failed: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def send_email_alert(subject: str, body: str) -> bool:
    """Send email alert for critical failures."""
    if not all([SMTP_USER, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO]):
        logger.warning("Email not configured, skipping")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        logger.info(f"Email alert sent to {EMAIL_TO}")
        return True
    except Exception as e:
        logger.error(f"Email alert failed: {e}")
        return False


def create_fix_pr(analysis: dict) -> str | None:
    """Create a PR with Claude's suggested fix."""
    fix = analysis.get("fix")
    if not fix or not fix.get("file") or not fix.get("old_code") or not fix.get("new_code"):
        return None

    file_path = fix["file"]
    # Safety: only fix Python files in the project
    if not file_path.endswith(".py"):
        logger.warning(f"Skipping fix for non-Python file: {file_path}")
        return None

    try:
        with open(file_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"Fix target file not found: {file_path}")
        return None

    if fix["old_code"] not in content:
        logger.error(f"Fix target code not found in {file_path}")
        return None

    # Create branch
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    branch = f"fix/monitor-{timestamp}"

    try:
        subprocess.run(["git", "checkout", "-b", branch], check=True, capture_output=True)

        new_content = content.replace(fix["old_code"], fix["new_code"], 1)
        with open(file_path, "w") as f:
            f.write(new_content)

        subprocess.run(["git", "add", file_path], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"Auto-fix: {fix['description']}\n\nGenerated by Valve Wire Monitor agent."],
            check=True, capture_output=True,
        )
        subprocess.run(["git", "push", "origin", branch], check=True, capture_output=True)

        result = subprocess.run(
            ["gh", "pr", "create",
             "--title", f"Auto-fix: {fix['description']}",
             "--body", f"## Auto-generated fix\n\n**Root cause:** {analysis.get('root_cause', 'Unknown')}\n\n"
                       f"**Fix:** {fix['description']}\n\n"
                       f"**File:** `{file_path}`\n\n"
                       f"Generated by the Valve Wire Monitor agent.\n\n"
                       f"⚠️ Review before merging.",
             "--label", "auto-fix",
             "--head", branch],
            check=True, capture_output=True, text=True,
        )
        pr_url = result.stdout.strip()
        logger.info(f"Fix PR created: {pr_url}")

        # Return to main
        subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
        return pr_url

    except subprocess.CalledProcessError as e:
        logger.error(f"Fix PR creation failed: {e.stderr}")
        subprocess.run(["git", "checkout", "main"], capture_output=True)
        return None


def format_telegram_message(analysis: dict, workflow_name: str, pr_url: str = None) -> str:
    """Format the Telegram notification message."""
    severity = analysis.get("severity", "UNKNOWN")
    summary = analysis.get("summary", "No summary")
    details = analysis.get("details", "")
    metrics = analysis.get("metrics", {})

    icon = {"OK": "✅", "WARNING": "⚠️", "ERROR": "❌", "CRITICAL": "🚨"}.get(severity, "❓")

    lines = [f"{icon} *{workflow_name}*", f"_{summary}_"]

    if details:
        lines.append(f"\n{details}")

    if metrics:
        parts = []
        if metrics.get("articles_new") is not None:
            parts.append(f"Articles: {metrics['articles_new']} new")
        if metrics.get("email_sent") is True:
            parts.append("Email: sent")
        elif metrics.get("email_sent") is False:
            parts.append("Email: FAILED")
        if metrics.get("duration_seconds"):
            mins = metrics["duration_seconds"] / 60
            parts.append(f"Duration: {mins:.1f}m")
        if parts:
            lines.append("\n" + " · ".join(parts))

    errors = analysis.get("errors", [])
    if errors:
        lines.append("\n*Errors:*")
        for e in errors[:5]:
            lines.append(f"• {e}")

    if pr_url:
        lines.append(f"\n🔧 *Auto-fix PR:* {pr_url}")

    if severity in ("ERROR", "CRITICAL"):
        lines.append("\n`/rerun` to retry · `/status` for details")

    return "\n".join(lines)


def main():
    logger.info(f"Monitor starting: {WORKFLOW_NAME} (run {WORKFLOW_RUN_ID}, {WORKFLOW_CONCLUSION})")

    if not WORKFLOW_RUN_ID:
        logger.error("No workflow run ID provided")
        return

    # 1. Fetch logs
    logs = fetch_workflow_logs(WORKFLOW_RUN_ID)
    if not logs:
        send_telegram(f"⚠️ *{WORKFLOW_NAME}*\n_Could not fetch workflow logs for analysis_")
        return

    # 2. Analyze with Claude
    analysis = analyze_logs(logs, WORKFLOW_NAME, WORKFLOW_CONCLUSION)
    severity = analysis.get("severity", "UNKNOWN")

    # 3. Attempt auto-fix if code bug detected
    pr_url = None
    if analysis.get("is_code_bug") and analysis.get("fix"):
        logger.info("Code bug detected, attempting auto-fix...")
        pr_url = create_fix_pr(analysis)

    # 4. Send Telegram notification
    telegram_msg = format_telegram_message(analysis, WORKFLOW_NAME, pr_url)
    send_telegram(telegram_msg)

    # 5. Send email for CRITICAL failures
    if severity == "CRITICAL":
        subject = f"[Valve Wire CRITICAL] {WORKFLOW_NAME} failed"
        body = (
            f"Workflow: {WORKFLOW_NAME}\n"
            f"Run ID: {WORKFLOW_RUN_ID}\n"
            f"Conclusion: {WORKFLOW_CONCLUSION}\n\n"
            f"Summary: {analysis.get('summary')}\n"
            f"Root cause: {analysis.get('root_cause', 'Unknown')}\n\n"
            f"Errors:\n" + "\n".join(f"  - {e}" for e in analysis.get("errors", [])) + "\n\n"
            f"https://github.com/{REPO}/actions/runs/{WORKFLOW_RUN_ID}"
        )
        if pr_url:
            body += f"\n\nAuto-fix PR: {pr_url}"
        send_email_alert(subject, body)

    logger.info(f"Monitor complete: {severity}")


if __name__ == "__main__":
    main()
