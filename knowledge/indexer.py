"""Index papers in knowledge/papers/ into papers_index.json.

Scans for unindexed PDFs, extracts text via PyMuPDF, uses Claude to extract
structured metadata, and updates the index. Also renames files descriptively.

Usage:
    python -m knowledge.indexer              # Index new papers only
    python -m knowledge.indexer --reindex    # Reindex all papers
    python -m knowledge.indexer --inbox      # Process inbox/ and index
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from pathlib import Path

import fitz  # PyMuPDF
from anthropic import Anthropic

import config

logger = logging.getLogger(__name__)

PAPERS_DIR = Path(__file__).parent / "papers"
INBOX_DIR = PAPERS_DIR / "inbox"
INDEX_PATH = Path(__file__).parent / "papers_index.json"

EXTRACTION_PROMPT = """\
You are a medical research librarian. Extract structured metadata from this \
academic paper about structural heart disease / valve therapy.

Return a JSON object with these fields:
- "title": Full paper title
- "authors": First author et al. (e.g., "Mack MJ et al.")
- "journal": Journal name (use standard abbreviations: NEJM, JACC, JAMA, etc.)
- "year": Publication year (integer)
- "study_design": One of: "Randomized controlled trial", "Meta-analysis", \
"Systematic review", "Prospective cohort", "Retrospective cohort", "Registry", \
"Case series", "Editorial/Commentary", "Guideline", "Other"
- "sample_size": Number of patients/subjects (integer, null if not applicable)
- "valve_type": One or more of: "aortic", "mitral", "tricuspid", "pulmonic", "general"
- "key_finding": 1-2 sentence summary of the main finding or conclusion
- "clinical_implications": 1 sentence on how this affects clinical practice
- "trial_name": Name of the trial if applicable (e.g., "PARTNER 3", "COAPT"), null otherwise
- "suggested_filename": A descriptive filename like "NEJM_2019_Mack_PARTNER3_LowRisk.pdf"

Return ONLY the JSON object. No other text.

## Paper Text (first 8000 characters)
{paper_text}"""


def extract_text_from_pdf(pdf_path: Path, max_chars: int = 8000) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    try:
        doc = fitz.open(str(pdf_path))
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
            if sum(len(t) for t in text_parts) > max_chars:
                break
        doc.close()
        text = "\n".join(text_parts)
        # Clean up common PDF artifacts
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text[:max_chars]
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path.name}: {e}")
        return ""


def extract_metadata_with_claude(paper_text: str) -> dict | None:
    """Use Claude to extract structured metadata from paper text."""
    if not paper_text or len(paper_text) < 100:
        return None

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    try:
        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": EXTRACTION_PROMPT.format(paper_text=paper_text),
            }],
            timeout=60.0,
        )

        raw = message.content[0].text.strip()
        # Handle markdown code blocks
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        return json.loads(raw)
    except Exception as e:
        logger.error(f"Claude metadata extraction failed: {e}")
        return None


def load_index() -> list[dict]:
    """Load the existing papers index."""
    if INDEX_PATH.exists():
        try:
            return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_index(index: list[dict]) -> None:
    """Save the papers index."""
    INDEX_PATH.write_text(
        json.dumps(index, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info(f"Saved index with {len(index)} papers to {INDEX_PATH.name}")


def get_indexed_files(index: list[dict]) -> set[str]:
    """Get the set of already-indexed filenames."""
    return {entry.get("original_filename", entry.get("filename", "")) for entry in index}


def process_inbox() -> list[Path]:
    """Move PDFs from inbox/ to papers/ and return the list of new files."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    moved = []
    for pdf in INBOX_DIR.glob("*.pdf"):
        dest = PAPERS_DIR / pdf.name
        if dest.exists():
            # Avoid overwriting — add suffix
            dest = PAPERS_DIR / f"{pdf.stem}_new{pdf.suffix}"
        pdf.rename(dest)
        moved.append(dest)
        logger.info(f"Moved from inbox: {pdf.name}")
    return moved


def rename_paper(pdf_path: Path, suggested_name: str) -> Path:
    """Rename a paper file to a descriptive name."""
    if not suggested_name:
        return pdf_path

    # Sanitize filename
    safe_name = re.sub(r'[^\w\-_.]', '_', suggested_name)
    if not safe_name.endswith('.pdf'):
        safe_name += '.pdf'

    new_path = pdf_path.parent / safe_name
    if new_path == pdf_path:
        return pdf_path
    if new_path.exists():
        logger.warning(f"Target filename already exists: {safe_name}, keeping original")
        return pdf_path

    pdf_path.rename(new_path)
    logger.info(f"Renamed: {pdf_path.name} → {safe_name}")
    return new_path


def index_papers(reindex: bool = False, process_inbox_first: bool = False) -> int:
    """Index new (or all) papers in knowledge/papers/.

    Args:
        reindex: If True, reindex all papers. If False, only new ones.
        process_inbox_first: If True, move files from inbox/ first.

    Returns:
        Number of papers newly indexed.
    """
    if process_inbox_first:
        new_from_inbox = process_inbox()
        if new_from_inbox:
            logger.info(f"Moved {len(new_from_inbox)} papers from inbox")

    index = load_index()
    indexed_files = get_indexed_files(index)

    if reindex:
        index = []
        indexed_files = set()
        logger.info("Reindexing all papers")

    # Find PDFs to process
    all_pdfs = sorted(PAPERS_DIR.glob("*.pdf"))
    to_process = [p for p in all_pdfs if p.name not in indexed_files]

    if not to_process:
        logger.info("No new papers to index")
        return 0

    logger.info(f"Indexing {len(to_process)} papers...")
    newly_indexed = 0

    for i, pdf_path in enumerate(to_process):
        logger.info(f"[{i + 1}/{len(to_process)}] Processing: {pdf_path.name}")

        # Extract text
        text = extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"  No text extracted, skipping")
            continue

        # Extract metadata via Claude
        metadata = extract_metadata_with_claude(text)
        if not metadata:
            logger.warning(f"  Metadata extraction failed, skipping")
            continue

        # Rename file
        original_name = pdf_path.name
        suggested = metadata.pop("suggested_filename", None)
        new_path = rename_paper(pdf_path, suggested)

        # Build index entry
        entry = {
            "filename": new_path.name,
            "original_filename": original_name,
            "title": metadata.get("title", ""),
            "authors": metadata.get("authors", ""),
            "journal": metadata.get("journal", ""),
            "year": metadata.get("year"),
            "study_design": metadata.get("study_design", ""),
            "sample_size": metadata.get("sample_size"),
            "valve_type": metadata.get("valve_type", "general"),
            "key_finding": metadata.get("key_finding", ""),
            "clinical_implications": metadata.get("clinical_implications", ""),
            "trial_name": metadata.get("trial_name"),
        }

        index.append(entry)
        newly_indexed += 1

        # Brief pause to avoid rate limiting
        if i < len(to_process) - 1:
            time.sleep(1)

    # Sort by year (newest first), then journal hierarchy
    journal_rank = {"NEJM": 1, "JAMA": 2, "JACC": 3, "Lancet": 4, "EHJ": 5}
    index.sort(key=lambda e: (
        -(e.get("year") or 0),
        journal_rank.get(e.get("journal", ""), 99),
    ))

    save_index(index)
    logger.info(f"Indexed {newly_indexed} new papers. Total: {len(index)}")
    return newly_indexed


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    reindex = "--reindex" in sys.argv
    inbox = "--inbox" in sys.argv or "--reindex" not in sys.argv

    count = index_papers(reindex=reindex, process_inbox_first=inbox)
    print(f"Done. Indexed {count} papers.")
