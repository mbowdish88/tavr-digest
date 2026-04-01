"""Knowledge base for The Valve Wire — guidelines and literature context."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).parent


def load_guidelines_context() -> str:
    """Load the guidelines summary as context for Claude prompts.

    This MUST be included in every digest, weekly summary, and podcast
    generation call. The guidelines provide the editorial framework for
    interpreting all new findings.
    """
    summary_path = KNOWLEDGE_DIR / "guidelines_summary.md"
    index_path = KNOWLEDGE_DIR / "guidelines_index.json"

    parts = []

    # Load the readable summary
    if summary_path.exists():
        summary = summary_path.read_text(encoding="utf-8")
        # Include the full guidelines — Claude's context window handles it easily
        parts.append(summary)
        logger.info(f"Loaded guidelines summary: {len(summary)} chars")

    # Load key disagreements from the index for quick reference
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            disagreements = index.get("guideline_disagreements", [])
            if disagreements:
                parts.append("\n## Key Guideline Disagreements (Quick Reference)")
                for d in disagreements:
                    topic = d.get("topic", "")
                    accaha = d.get("acc_aha", "")
                    esc = d.get("esc", "")
                    parts.append(f"- **{topic}**: ACC/AHA: {accaha} | ESC: {esc}")
        except Exception as e:
            logger.warning(f"Could not load guidelines index: {e}")

    if not parts:
        logger.warning("No guidelines knowledge base found")
        return ""

    context = (
        "## MANDATORY EDITORIAL CONTEXT: Current Valve Guidelines\n"
        "The following summarizes the 2020 ACC/AHA and 2025 ESC/EACTS valve guidelines. "
        "ALL analysis must be interpreted in light of these guidelines. When reporting "
        "on new findings, explicitly reference how they relate to current guideline "
        "recommendations, especially where ACC/AHA and ESC disagree.\n\n"
    )
    context += "\n".join(parts)

    return context


def load_papers_context() -> str:
    """Load indexed papers as context (when available).

    Returns empty string if no papers have been indexed yet.
    """
    papers_index = KNOWLEDGE_DIR / "papers_index.json"
    if not papers_index.exists():
        return ""

    try:
        papers = json.loads(papers_index.read_text(encoding="utf-8"))
        if not papers:
            return ""

        parts = [
            "## Reference Literature\n"
            "The following landmark studies inform our editorial analysis:\n"
        ]
        for paper in papers[:20]:  # Cap at 20 papers
            title = paper.get("title", "")
            key_finding = paper.get("key_finding", "")
            parts.append(f"- **{title}**: {key_finding}")

        return "\n".join(parts)
    except Exception as e:
        logger.warning(f"Could not load papers index: {e}")
        return ""


def get_full_knowledge_context() -> str:
    """Get the complete knowledge context for Claude prompts.

    This combines guidelines + papers into one block that should be
    appended to every Claude system prompt.
    """
    parts = []

    guidelines = load_guidelines_context()
    if guidelines:
        parts.append(guidelines)

    papers = load_papers_context()
    if papers:
        parts.append(papers)

    if not parts:
        return ""

    return "\n\n---\n\n".join(parts)
