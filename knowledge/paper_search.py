#!/usr/bin/env python3
"""
Standalone PubMed paper search and download script for structural heart disease.

============================================================================
IMPORTANT: This script MUST be run from a computer with institutional journal
access (e.g., Cedars-Sinai network). PMC and journal publishers block PDF
downloads from home/personal networks — even for "open access" papers.

Options for running at Cedars:
  1. Cowork — give it this script, tell it to run it
  2. Office computer on Cedars network — run directly
  3. Cedars VPN from home — connect first, then run

After downloading, copy the PDFs back to:
  ~/projects/tavr-digest/knowledge/papers/inbox/
Then run: python -m knowledge.indexer
The indexer will catalog, rename, and integrate them into the knowledge base.
============================================================================

This script is SELF-CONTAINED — one file, no project dependencies.
Copy it to any machine and run it. Only needs: Python 3.8+ and `requests`.

Setup (one time):
    pip install requests

Usage:
    python paper_search.py                    # Full search + download
    python paper_search.py --dry-run          # Search only, no downloads
    python paper_search.py --csv-only         # Search + CSV report only
    python paper_search.py --authors-only     # Only author-based searches
    python paper_search.py --topics-only      # Only topic-based searches
    python paper_search.py --since 2020       # Override start year
    python paper_search.py --limit 100        # Limit total downloads
    python paper_search.py --output-dir /path # Override output directory

Output:
    ./inbox/                              # Downloaded PDFs (or --output-dir)
    ./paper_search_results.csv            # Full metadata for all papers found
    ./needs_institutional_access.txt      # Papers that couldn't be downloaded
"""

import argparse
import csv
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from xml.etree import ElementTree

import requests

# ---------------------------------------------------------------------------
# Configuration (self-contained -- no imports from the project)
# ---------------------------------------------------------------------------

NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")  # optional but recommended
NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PMC_PDF_BASE = "https://www.ncbi.nlm.nih.gov/pmc/articles"

# Rate limiting: NCBI allows 3 req/s without key, 10 req/s with key
REQUEST_DELAY = 0.12 if NCBI_API_KEY else 0.4

DEFAULT_START_YEAR = 2005
DEFAULT_END_YEAR = 2026

# -- Authors ----------------------------------------------------------------

AUTHORS_INTERVENTIONAL = [
    "Mack MJ", "Leon MB", "Thourani VH", "Makkar R", "Makkar RR",
    "Kodali SK", "Hahn RT", "Genereux P", "Smith CR", "Coylewright M",
    "Forrest JK", "Deeb GM", "Reardon MJ", "Stone GW", "Sorajja P",
    "Feldman T", "Sondergaard L",
]

AUTHORS_SURGICAL = [
    "Bowdish ME", "Badhwar V", "Mehaffey JH", "Kaul S", "Miller DC",
    "Chikwe J", "Bavaria JE", "Borger MA", "Mesana T", "Moon MR",
    "Suri RM",
]

ALL_AUTHORS = AUTHORS_INTERVENTIONAL + AUTHORS_SURGICAL

# -- Journals ---------------------------------------------------------------

JOURNALS_TIER1 = [
    "N Engl J Med",
    "JAMA",
    "JAMA Cardiol",
    "Lancet",
    "J Am Coll Cardiol",
]

JOURNALS_TIER2 = [
    "Eur Heart J",
    "Circulation",
    "JACC Cardiovasc Interv",
]

JOURNALS_TIER3 = [
    "Ann Thorac Surg",
    "J Thorac Cardiovasc Surg",
    "Eur J Cardiothorac Surg",
]

ALL_JOURNALS = JOURNALS_TIER1 + JOURNALS_TIER2 + JOURNALS_TIER3

# -- Topic queries ----------------------------------------------------------

LANDMARK_TRIALS_QUERY = (
    '("PARTNER" OR "COAPT" OR "MITRA-FR" OR "TRILUMINATE" OR "TRISCEND" '
    'OR "CLASP" OR "SURTAVI" OR "CoreValve" OR "NOTION" OR "DEDICATE" '
    'OR "EARLY TAVR" OR "EVOLVED" OR "SAPIEN" OR "RECOVERY" OR "AVATAR" '
    'OR "REPRISE" OR "PROTECTED TAVR" OR "ENVISAGE" OR "UK TAVI" '
    'OR "APOLLO" OR "ACURATE" OR "FORWARD" OR "UNLOAD")'
)

TOPIC_QUERIES = {
    "aortic_tavr_vs_savr": (
        '("TAVR" OR "TAVI" OR "transcatheter aortic") AND '
        '("surgical" OR "SAVR") AND ("comparison" OR "outcomes" OR "randomized")'
    ),
    "aortic_bicuspid": (
        '("bicuspid" OR "BAV") AND ("TAVR" OR "TAVI" OR "aortic valve replacement")'
    ),
    "aortic_low_risk": (
        '("low risk" OR "low-risk") AND ("TAVR" OR "TAVI") AND ("aortic stenosis")'
    ),
    "mitral_transcatheter": (
        '("MitraClip" OR "PASCAL" OR "transcatheter mitral" OR "TEER" '
        'OR "edge-to-edge") AND ("mitral regurgitation")'
    ),
    "mitral_surgical": (
        '("mitral valve repair" OR "mitral valve replacement") AND '
        '("outcomes" OR "randomized" OR "comparison")'
    ),
    "tricuspid_transcatheter": (
        '("TriClip" OR "PASCAL" OR "transcatheter tricuspid" OR "TTVR" '
        'OR "tricuspid TEER") AND ("tricuspid regurgitation")'
    ),
    "tricuspid_surgical": (
        '("tricuspid valve surgery" OR "tricuspid annuloplasty" OR "tricuspid repair") '
        'AND ("outcomes")'
    ),
    "durability": (
        '("structural valve deterioration" OR "SVD" OR "bioprosthetic" '
        'OR "durability" OR "long-term") AND ("TAVR" OR "TAVI" OR "transcatheter")'
    ),
    "guidelines": (
        '("guideline" OR "consensus" OR "expert consensus" OR "appropriate use") '
        'AND ("valvular heart disease" OR "aortic stenosis" OR "mitral regurgitation" '
        'OR "tricuspid")'
    ),
    "surgical_outcomes_sts": (
        '("STS database" OR "STS registry" OR "surgical outcomes") AND '
        '("aortic valve" OR "mitral valve" OR "tricuspid valve")'
    ),
}

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("paper_search")

# ---------------------------------------------------------------------------
# NCBI E-utilities helpers
# ---------------------------------------------------------------------------


def _api_params() -> Dict[str, str]:
    """Return common API parameters."""
    params = {"retmode": "xml"}
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    return params


def _throttle():
    """Sleep to respect NCBI rate limits."""
    time.sleep(REQUEST_DELAY)


def _build_journal_filter() -> str:
    """Build a PubMed journal filter string."""
    parts = [f'"{j}"[Journal]' for j in ALL_JOURNALS]
    return "(" + " OR ".join(parts) + ")"


def esearch(query: str, retmax: int = 5000) -> List[str]:
    """Run an ESearch query and return a list of PMIDs."""
    params = {
        **_api_params(),
        "db": "pubmed",
        "term": query,
        "retmax": str(retmax),
        "usehistory": "n",
    }
    _throttle()
    try:
        resp = requests.get(f"{NCBI_BASE}/esearch.fcgi", params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.error(f"ESearch failed for query: {query[:80]}... -- {e}")
        return []

    root = ElementTree.fromstring(resp.content)
    pmids = [id_elem.text for id_elem in root.findall(".//Id") if id_elem.text]
    return pmids


def efetch_details(pmids: List[str]) -> List[Dict]:
    """Fetch article metadata for a batch of PMIDs (max 200 at a time)."""
    articles = []
    for i in range(0, len(pmids), 200):
        batch = pmids[i : i + 200]
        params = {
            **_api_params(),
            "db": "pubmed",
            "id": ",".join(batch),
            "rettype": "xml",
        }
        _throttle()
        try:
            resp = requests.get(f"{NCBI_BASE}/efetch.fcgi", params=params, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as e:
            log.error(f"EFetch failed for batch starting at index {i}: {e}")
            continue

        root = ElementTree.fromstring(resp.content)
        for article_elem in root.findall(".//PubmedArticle"):
            parsed = _parse_article(article_elem)
            if parsed:
                articles.append(parsed)

    return articles


def _parse_article(elem) -> Optional[Dict]:
    """Parse a PubmedArticle XML element into a dict."""
    try:
        medline = elem.find(".//MedlineCitation")
        if medline is None:
            return None

        pmid_elem = medline.find("PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""

        article = medline.find("Article")
        if article is None:
            return None

        # Title
        title_elem = article.find("ArticleTitle")
        title = _extract_text(title_elem) if title_elem is not None else ""

        # Journal
        journal_abbrev_elem = article.find(".//Journal/ISOAbbreviation")
        journal_elem = article.find(".//Journal/Title")
        journal = ""
        if journal_abbrev_elem is not None and journal_abbrev_elem.text:
            journal = journal_abbrev_elem.text.rstrip(".")
        elif journal_elem is not None and journal_elem.text:
            journal = journal_elem.text

        # Date
        pub_date = article.find(".//Journal/JournalIssue/PubDate")
        year = ""
        month = ""
        if pub_date is not None:
            year_elem = pub_date.find("Year")
            month_elem = pub_date.find("Month")
            medline_date = pub_date.find("MedlineDate")
            if year_elem is not None and year_elem.text:
                year = year_elem.text
            elif medline_date is not None and medline_date.text:
                match = re.match(r"(\d{4})", medline_date.text)
                if match:
                    year = match.group(1)
            if month_elem is not None and month_elem.text:
                month = month_elem.text

        # Authors
        authors = []
        for author_elem in article.findall(".//AuthorList/Author"):
            last = author_elem.find("LastName")
            initials = author_elem.find("Initials")
            if last is not None and last.text:
                name = last.text
                if initials is not None and initials.text:
                    name += " " + initials.text
                authors.append(name)

        first_author = authors[0] if authors else "Unknown"
        first_author_last = first_author.split()[0] if first_author != "Unknown" else "Unknown"

        # DOI
        doi = ""
        for id_elem in article.findall(".//ELocationID"):
            if id_elem.get("EIdType") == "doi" and id_elem.text:
                doi = id_elem.text
                break
        if not doi:
            article_data = elem.find(".//PubmedData")
            if article_data is not None:
                for id_elem in article_data.findall(".//ArticleId"):
                    if id_elem.get("IdType") == "doi" and id_elem.text:
                        doi = id_elem.text
                        break

        # PMC ID
        pmc_id = ""
        article_data = elem.find(".//PubmedData")
        if article_data is not None:
            for id_elem in article_data.findall(".//ArticleId"):
                if id_elem.get("IdType") == "pmc" and id_elem.text:
                    pmc_id = id_elem.text
                    break

        return {
            "pmid": pmid,
            "title": title,
            "journal": journal,
            "year": year,
            "month": month,
            "first_author": first_author,
            "first_author_last": first_author_last,
            "authors": "; ".join(authors),
            "doi": doi,
            "pmc_id": pmc_id,
            "pdf_available": bool(pmc_id),
            "pdf_downloaded": False,
            "pdf_filename": "",
            "search_sources": set(),
        }
    except Exception as e:
        log.warning(f"Failed to parse article: {e}")
        return None


def _extract_text(elem) -> str:
    """Extract all text from an element, including mixed content (e.g. <i> tags)."""
    return "".join(elem.itertext()).strip()


# ---------------------------------------------------------------------------
# Search orchestration
# ---------------------------------------------------------------------------


def search_by_author(author: str, journal_filter: str, date_range: str) -> List[str]:
    """Search PubMed for papers by a specific author in target journals."""
    query = f'"{author}"[Author] AND {journal_filter} AND {date_range}[dp]'
    pmids = esearch(query)
    log.info(f"  Author '{author}': {len(pmids)} results")
    return pmids


def search_by_topic(name: str, topic_query: str, journal_filter: str, date_range: str) -> List[str]:
    """Search PubMed for papers matching a topic query in target journals."""
    query = f"{topic_query} AND {journal_filter} AND {date_range}[dp]"
    pmids = esearch(query)
    log.info(f"  Topic '{name}': {len(pmids)} results")
    return pmids


def run_all_searches(
    max_results: int = 5000,
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR,
    authors_only: bool = False,
    topics_only: bool = False,
) -> Dict[str, Dict]:
    """Run all author + topic searches, deduplicate by PMID, fetch metadata."""
    journal_filter = _build_journal_filter()
    date_range = f"{start_year}:{end_year}"
    pmid_sources: Dict[str, Set[str]] = {}

    # Author searches
    if not topics_only:
        log.info("=== Running author searches ===")
        for author in ALL_AUTHORS:
            pmids = search_by_author(author, journal_filter, date_range)
            for pmid in pmids:
                if pmid not in pmid_sources:
                    pmid_sources[pmid] = set()
                pmid_sources[pmid].add(f"author:{author}")

    if not authors_only:
        # Landmark trials
        log.info("=== Running landmark trials search ===")
        pmids = search_by_topic("landmark_trials", LANDMARK_TRIALS_QUERY, journal_filter, date_range)
        for pmid in pmids:
            if pmid not in pmid_sources:
                pmid_sources[pmid] = set()
            pmid_sources[pmid].add("topic:landmark_trials")

        # Topic searches
        log.info("=== Running topic searches ===")
        for name, query in TOPIC_QUERIES.items():
            pmids = search_by_topic(name, query, journal_filter, date_range)
            for pmid in pmids:
                if pmid not in pmid_sources:
                    pmid_sources[pmid] = set()
                pmid_sources[pmid].add(f"topic:{name}")

    all_pmids = list(pmid_sources.keys())
    log.info(f"\nTotal unique PMIDs found: {len(all_pmids)}")

    # Fetch metadata
    log.info("=== Fetching article metadata ===")
    articles = efetch_details(all_pmids)

    # Merge source info
    articles_by_pmid: Dict[str, Dict] = {}
    for art in articles:
        pmid = art["pmid"]
        art["search_sources"] = pmid_sources.get(pmid, set())

        has_author = any(s.startswith("author:") for s in art["search_sources"])
        has_topic = any(s.startswith("topic:") for s in art["search_sources"])
        if has_author and has_topic:
            art["search_source_type"] = "Both"
        elif has_author:
            art["search_source_type"] = "Author"
        else:
            art["search_source_type"] = "Topic"

        articles_by_pmid[pmid] = art

    log.info(f"Metadata fetched for {len(articles_by_pmid)} articles")
    return articles_by_pmid


# ---------------------------------------------------------------------------
# PDF download
# ---------------------------------------------------------------------------


def download_pdf_from_pmc(pmc_id: str, output_path: Path) -> bool:
    """Attempt to download a PDF from PubMed Central."""
    url = f"{PMC_PDF_BASE}/{pmc_id}/pdf/"
    try:
        _throttle()
        resp = requests.get(url, timeout=60, allow_redirects=True)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith(
            "application/pdf"
        ):
            output_path.write_bytes(resp.content)
            return True
        # Try alternate URL pattern
        url_alt = f"{PMC_PDF_BASE}/{pmc_id}/pdf/main.pdf"
        _throttle()
        resp = requests.get(url_alt, timeout=60, allow_redirects=True)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith(
            "application/pdf"
        ):
            output_path.write_bytes(resp.content)
            return True
    except requests.RequestException as e:
        log.debug(f"PMC download failed for {pmc_id}: {e}")
    return False


def download_pdf_from_doi(doi: str, output_path: Path) -> bool:
    """Attempt to download a PDF via DOI redirect (works with institutional access)."""
    if not doi:
        return False
    url = f"https://doi.org/{doi}"
    headers = {
        "Accept": "application/pdf",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        _throttle()
        resp = requests.get(
            url, headers=headers, timeout=60, allow_redirects=True, stream=True
        )
        content_type = resp.headers.get("content-type", "")
        if resp.status_code == 200 and "pdf" in content_type.lower():
            output_path.write_bytes(resp.content)
            return True
    except requests.RequestException as e:
        log.debug(f"DOI download failed for {doi}: {e}")
    return False


def download_papers(
    articles: Dict[str, Dict], output_dir: Path, dry_run: bool = False,
    limit: Optional[int] = None,
) -> Tuple[int, int, List[Dict]]:
    """Download available PDFs. Returns (downloaded_count, failed_count, needs_access_list)."""
    downloaded = 0
    failed = 0
    needs_access = []

    items = list(articles.items())
    if limit is not None:
        items = items[:limit]
    total = len(items)
    for i, (pmid, art) in enumerate(items, 1):
        year = art.get("year", "XXXX")
        author_last = re.sub(r"[^\w]", "", art.get("first_author_last", "Unknown"))
        journal_short = _journal_shortname(art.get("journal", ""))
        filename = f"{year}_{author_last}_{journal_short}_{pmid}.pdf"
        output_path = output_dir / filename

        if output_path.exists():
            art["pdf_downloaded"] = True
            art["pdf_filename"] = filename
            log.debug(f"[{i}/{total}] Already exists: {filename}")
            downloaded += 1
            continue

        if dry_run:
            if art.get("pmc_id"):
                art["pdf_available"] = True
            continue

        success = False

        # Try PMC first
        if art.get("pmc_id"):
            log.info(f"[{i}/{total}] Downloading from PMC: {art['pmc_id']} -> {filename}")
            success = download_pdf_from_pmc(art["pmc_id"], output_path)

        # Try DOI if PMC failed
        if not success and art.get("doi"):
            log.info(f"[{i}/{total}] Trying DOI: {art['doi']} -> {filename}")
            success = download_pdf_from_doi(art["doi"], output_path)

        if success:
            art["pdf_downloaded"] = True
            art["pdf_filename"] = filename
            downloaded += 1
            log.info(f"  -> Downloaded successfully")
        else:
            failed += 1
            needs_access.append(art)
            if i % 50 == 0:
                log.info(f"  Progress: {i}/{total} checked, {downloaded} downloaded")

    return downloaded, failed, needs_access


def _journal_shortname(journal: str) -> str:
    """Convert journal name to a short filename-safe label."""
    mapping = {
        "N Engl J Med": "NEJM",
        "New Engl J Med": "NEJM",
        "JAMA": "JAMA",
        "JAMA Cardiol": "JAMACardiol",
        "Lancet": "Lancet",
        "J Am Coll Cardiol": "JACC",
        "Eur Heart J": "EHJ",
        "Circulation": "Circ",
        "JACC Cardiovasc Interv": "JACCIntv",
        "JACC. Cardiovascular interventions": "JACCIntv",
        "Ann Thorac Surg": "ATS",
        "J Thorac Cardiovasc Surg": "JTCVS",
        "Eur J Cardiothorac Surg": "EJCTS",
    }
    for key, short in mapping.items():
        if key.lower() in journal.lower():
            return short
    return re.sub(r"[^\w]", "", journal)[:12]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_needs_access(needs_access: List[Dict], output_dir: Path) -> None:
    """Write a list of papers that need institutional access to download."""
    output_file = output_dir / "needs_institutional_access.txt"
    with open(output_file, "w") as f:
        f.write("# Papers requiring institutional access for PDF download\n")
        f.write(f"# Generated by paper_search.py\n")
        f.write(f"# Total: {len(needs_access)} papers\n\n")

        tier1 = [a for a in needs_access if
                 any(j.lower() in a.get("journal", "").lower() for j in JOURNALS_TIER1)]
        tier2 = [a for a in needs_access if a not in tier1 and
                 any(j.lower() in a.get("journal", "").lower() for j in JOURNALS_TIER2)]
        tier3 = [a for a in needs_access if a not in tier1 and a not in tier2]

        for label, group in [("TIER 1 (highest priority)", tier1),
                             ("TIER 2", tier2),
                             ("TIER 3", tier3)]:
            if not group:
                continue
            f.write(f"\n=== {label} ({len(group)} papers) ===\n\n")
            for art in sorted(group, key=lambda x: x.get("year", "0"), reverse=True):
                f.write(f"PMID: {art['pmid']}\n")
                f.write(f"  Title: {art['title']}\n")
                f.write(f"  Journal: {art['journal']} ({art.get('year', '?')})\n")
                f.write(f"  Authors: {art['first_author']} et al.\n")
                if art.get("doi"):
                    f.write(f"  DOI: https://doi.org/{art['doi']}\n")
                f.write(f"  PubMed: https://pubmed.ncbi.nlm.nih.gov/{art['pmid']}/\n")
                f.write("\n")

    log.info(f"Wrote {len(needs_access)} papers to {output_file}")


def write_master_csv(articles: Dict[str, Dict], output_dir: Path) -> None:
    """Write a CSV master list of all found papers."""
    output_file = output_dir / "paper_search_results.csv"
    fieldnames = [
        "pmid", "title", "journal", "year", "month", "first_author",
        "authors", "doi", "pmc_id", "pdf_available", "pdf_downloaded",
        "pdf_filename", "pubmed_url", "doi_url", "search_source_type",
    ]

    rows = []
    for pmid, art in articles.items():
        row = {k: art.get(k, "") for k in fieldnames}
        row["pubmed_url"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        row["doi_url"] = f"https://doi.org/{art['doi']}" if art.get("doi") else ""
        row["pdf_available"] = "Yes" if art.get("pdf_available") or art.get("pmc_id") else "No"
        row["pdf_downloaded"] = "Yes" if art.get("pdf_downloaded") else "No"
        rows.append(row)

    def sort_key(r):
        journal = r.get("journal", "")
        if any(j.lower() in journal.lower() for j in JOURNALS_TIER1):
            tier = 1
        elif any(j.lower() in journal.lower() for j in JOURNALS_TIER2):
            tier = 2
        else:
            tier = 3
        year = r.get("year", "0")
        return (tier, -int(year) if year.isdigit() else 0)

    rows.sort(key=sort_key)

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    log.info(f"Wrote {len(rows)} papers to {output_file}")


def print_summary(articles: Dict[str, Dict], downloaded: int, failed: int) -> None:
    """Print a summary of search results."""
    total = len(articles)

    by_journal: Dict[str, int] = {}
    for art in articles.values():
        j = art.get("journal", "Unknown")
        by_journal[j] = by_journal.get(j, 0) + 1

    by_type = {"Author": 0, "Topic": 0, "Both": 0}
    for art in articles.values():
        t = art.get("search_source_type", "Topic")
        by_type[t] = by_type.get(t, 0) + 1

    with_pmc = sum(1 for a in articles.values() if a.get("pmc_id"))

    print("\n" + "=" * 60)
    print("PAPER SEARCH SUMMARY")
    print("=" * 60)
    print(f"Total unique papers found:  {total}")
    print(f"With PMC (free text):       {with_pmc}")
    print(f"PDFs downloaded:            {downloaded}")
    print(f"Need institutional access:  {failed}")
    print()
    print("By search type:")
    for t, c in sorted(by_type.items()):
        print(f"  {t}: {c}")
    print()
    print("By journal (top 15):")
    for j, c in sorted(by_journal.items(), key=lambda x: -x[1])[:15]:
        print(f"  {j}: {c}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Search PubMed and download structural heart disease papers."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save PDFs (default: knowledge/papers/inbox/ relative to script)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search only, do not download PDFs",
    )
    parser.add_argument(
        "--csv-only",
        action="store_true",
        help="Only write CSV results, skip PDF downloads",
    )
    parser.add_argument(
        "--authors-only",
        action="store_true",
        help="Only run author-based searches",
    )
    parser.add_argument(
        "--topics-only",
        action="store_true",
        help="Only run topic-based searches",
    )
    parser.add_argument(
        "--since",
        type=int,
        default=DEFAULT_START_YEAR,
        metavar="YEAR",
        help=f"Start year for searches (default: {DEFAULT_START_YEAR})",
    )
    parser.add_argument(
        "--until",
        type=int,
        default=DEFAULT_END_YEAR,
        metavar="YEAR",
        help=f"End year for searches (default: {DEFAULT_END_YEAR})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Limit total number of downloads",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5000,
        help="Max results per search query (default: 5000)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    if args.authors_only and args.topics_only:
        parser.error("Cannot use --authors-only and --topics-only together")

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        script_dir = Path(__file__).resolve().parent
        output_dir = script_dir / "papers" / "inbox"

    output_dir.mkdir(parents=True, exist_ok=True)
    log.info(f"Output directory: {output_dir}")

    if not NCBI_API_KEY:
        log.warning(
            "No NCBI_API_KEY set. Requests will be rate-limited to 3/sec. "
            "Set NCBI_API_KEY env var for 10/sec. "
            "Get a free key at: https://www.ncbi.nlm.nih.gov/account/settings/"
        )

    # Run searches
    articles = run_all_searches(
        max_results=args.max_results,
        start_year=args.since,
        end_year=args.until,
        authors_only=args.authors_only,
        topics_only=args.topics_only,
    )

    if not articles:
        log.error("No articles found. Check your network connection and try again.")
        sys.exit(1)

    # Write CSV
    write_master_csv(articles, output_dir)

    # Download PDFs
    if args.dry_run or args.csv_only:
        downloaded, failed = 0, 0
        needs_access = [a for a in articles.values() if not a.get("pmc_id")]
    else:
        downloaded, failed, needs_access = download_papers(
            articles, output_dir, dry_run=args.dry_run, limit=args.limit
        )

    # Write needs-access list
    if needs_access:
        write_needs_access(needs_access, output_dir)

    # Summary
    print_summary(articles, downloaded, failed)


if __name__ == "__main__":
    main()
