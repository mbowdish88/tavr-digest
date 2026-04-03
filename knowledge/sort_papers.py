#!/usr/bin/env python3
"""Interactive paper sorter — quickly triage inbox papers into verified or excluded.

Usage:
    python -m knowledge.sort_papers              # Sort all inbox papers
    python -m knowledge.sort_papers --indexed     # Only sort papers that have been indexed
    python -m knowledge.sort_papers --unindexed   # Only sort papers not yet indexed
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent
PAPERS_DIR = KNOWLEDGE_DIR / "papers"
INBOX_DIR = PAPERS_DIR / "inbox"
VERIFIED_DIR = PAPERS_DIR / "verified"
EXCLUDED_DIR = PAPERS_DIR / "excluded"
INDEX_PATH = KNOWLEDGE_DIR / "papers_index.json"


def load_index() -> dict[str, dict]:
    """Load papers index, keyed by filename."""
    if not INDEX_PATH.exists():
        return {}
    try:
        papers = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        by_file = {}
        for p in papers:
            for key in ("filename", "original_filename"):
                if p.get(key):
                    by_file[p[key]] = p
        return by_file
    except Exception:
        return {}


def get_metadata(filename: str, index: dict[str, dict]) -> dict:
    """Get metadata for a paper from the index."""
    return index.get(filename, {})


def display_paper(i: int, total: int, filename: str, meta: dict) -> None:
    """Display paper info for sorting."""
    print(f"\n{'=' * 60}")
    print(f"[{i}/{total}]  {filename}")
    print(f"{'=' * 60}")

    if meta:
        title = meta.get("title", "Unknown title")
        journal = meta.get("journal", "?")
        year = meta.get("year", "?")
        authors = meta.get("authors", "?")
        design = meta.get("study_design", "?")
        valve = meta.get("valve_type", "?")
        trial = meta.get("trial_name", "")
        finding = meta.get("key_finding", "No finding extracted")
        implications = meta.get("clinical_implications", "")

        print(f"\n  Title:    {title}")
        print(f"  Journal:  {journal} ({year})")
        print(f"  Authors:  {authors}")
        print(f"  Design:   {design}")
        print(f"  Valve:    {valve}")
        if trial:
            print(f"  Trial:    {trial}")
        print(f"\n  Finding:  {finding}")
        if implications:
            print(f"  Impact:   {implications}")
    else:
        print("\n  ⚠ Not yet indexed — no metadata available")
        print(f"  File size: {(INBOX_DIR / filename).stat().st_size / 1024:.0f} KB")

    print()
    print("  [v] Verified (relevant to structural heart)")
    print("  [e] Excluded (not relevant)")
    print("  [s] Skip (decide later)")
    print("  [o] Open PDF")
    print("  [q] Quit")


def open_pdf(filepath: Path) -> None:
    """Open a PDF in the default viewer."""
    import subprocess
    import platform
    if platform.system() == "Darwin":
        subprocess.Popen(["open", str(filepath)])
    elif platform.system() == "Linux":
        subprocess.Popen(["xdg-open", str(filepath)])
    else:
        subprocess.Popen(["start", str(filepath)], shell=True)


def sort_papers(indexed_only: bool = False, unindexed_only: bool = False) -> None:
    """Interactive sorting of inbox papers."""
    VERIFIED_DIR.mkdir(parents=True, exist_ok=True)
    EXCLUDED_DIR.mkdir(parents=True, exist_ok=True)

    index = load_index()

    # Get PDFs in inbox
    pdfs = sorted(INBOX_DIR.glob("*.pdf"))
    if not pdfs:
        print("No PDFs in inbox to sort.")
        return

    # Filter by indexed status if requested
    if indexed_only:
        pdfs = [p for p in pdfs if p.name in index]
    elif unindexed_only:
        pdfs = [p for p in pdfs if p.name not in index]

    if not pdfs:
        print("No matching PDFs found.")
        return

    total = len(pdfs)
    verified_count = 0
    excluded_count = 0
    skipped_count = 0

    print(f"\n📄 {total} papers to sort in inbox")
    print(f"   {len(index)} have been indexed with metadata\n")

    for i, pdf in enumerate(pdfs, 1):
        meta = get_metadata(pdf.name, index)
        display_paper(i, total, pdf.name, meta)

        while True:
            try:
                choice = input("  > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n\nQuitting.")
                break

            if choice == "v":
                dest = VERIFIED_DIR / pdf.name
                pdf.rename(dest)
                verified_count += 1
                print(f"  → Moved to verified/")
                break
            elif choice == "e":
                dest = EXCLUDED_DIR / pdf.name
                pdf.rename(dest)
                excluded_count += 1
                print(f"  → Moved to excluded/")
                break
            elif choice == "s":
                skipped_count += 1
                print(f"  → Skipped")
                break
            elif choice == "o":
                open_pdf(pdf)
                print(f"  → Opening PDF...")
                continue
            elif choice == "q":
                print(f"\n{'=' * 60}")
                print(f"Session summary:")
                print(f"  Verified:  {verified_count}")
                print(f"  Excluded:  {excluded_count}")
                print(f"  Skipped:   {skipped_count}")
                print(f"  Remaining: {total - i}")
                print(f"{'=' * 60}")
                return
            else:
                print("  Invalid choice. Use v/e/s/o/q")
                continue
        else:
            continue

    print(f"\n{'=' * 60}")
    print(f"Done! All {total} papers sorted:")
    print(f"  Verified:  {verified_count}")
    print(f"  Excluded:  {excluded_count}")
    print(f"  Skipped:   {skipped_count}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    indexed_only = "--indexed" in sys.argv
    unindexed_only = "--unindexed" in sys.argv
    sort_papers(indexed_only=indexed_only, unindexed_only=unindexed_only)
