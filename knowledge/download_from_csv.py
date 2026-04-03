#!/usr/bin/env python3
"""Download PDFs from a pre-filtered CSV — skips PubMed search, just downloads.

Usage:
    python knowledge/download_from_csv.py                           # Use filtered CSV
    python knowledge/download_from_csv.py --csv path/to/file.csv    # Custom CSV
    python knowledge/download_from_csv.py --limit 100               # Limit downloads
"""

import argparse
import csv
import io
import logging
import os
import re
import tarfile
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
DEFAULT_CSV = SCRIPT_DIR / "papers" / "inbox" / "paper_search_results_filtered.csv"
DEFAULT_OUTPUT = SCRIPT_DIR / "papers" / "inbox"

NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")
RATE_DELAY = 0.11 if NCBI_API_KEY else 0.34

BLOCKED_DOMAINS = [
    "nejm.org", "jacc.org", "elsevier.com", "thelancet.com",
    "ahajournals.org", "oup.com", "academic.oup.com", "doi.org",
    "annalsthoracicsurgery.org", "jtcvs.org",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (the-valve-wire/1.0; structural-heart-research)"
}


def is_blocked_url(url: str) -> bool:
    return any(d in url for d in BLOCKED_DOMAINS)


def is_valid_pdf(data: bytes) -> bool:
    return data[:5] == b"%PDF-"


def try_pmc_ftp(session: requests.Session, pmc_id: str, dest: Path) -> bool:
    """Download via PMC OA FTP service (tar.gz packages)."""
    if not pmc_id:
        return False
    pmc_num = pmc_id.replace("PMC", "")
    oa_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC{pmc_num}"
    try:
        resp = session.get(oa_url, timeout=15)
        href_match = re.search(r'href="([^"]+)"', resp.text)
        if not href_match:
            return False
        pkg_url = href_match.group(1).replace("ftp://ftp.ncbi.nlm.nih.gov/", "https://ftp.ncbi.nlm.nih.gov/")
        pkg_resp = session.get(pkg_url, timeout=60)
        if pkg_resp.status_code != 200:
            return False
        tar = tarfile.open(fileobj=io.BytesIO(pkg_resp.content), mode="r:gz")
        pdf_members = [m for m in tar.getmembers() if m.name.endswith(".pdf") and "supp" not in m.name.lower()]
        if pdf_members:
            pdf_data = tar.extractfile(pdf_members[0]).read()
            if is_valid_pdf(pdf_data):
                dest.write_bytes(pdf_data)
                tar.close()
                return True
        tar.close()
    except Exception as e:
        logger.debug(f"PMC FTP failed for {pmc_id}: {e}")
    return False


def try_unpaywall(session: requests.Session, doi: str, dest: Path) -> bool:
    """Download via Unpaywall repository copies."""
    if not doi:
        return False
    try:
        resp = session.get(
            f"https://api.unpaywall.org/v2/{doi}?email=thevalvewire@gmail.com",
            timeout=10,
        )
        if resp.status_code != 200:
            return False
        data = resp.json()
        for loc in data.get("oa_locations") or []:
            if loc.get("host_type") == "repository" and loc.get("url_for_pdf"):
                url = loc["url_for_pdf"]
                if is_blocked_url(url):
                    continue
                pdf_resp = session.get(url, timeout=30, headers=HEADERS)
                if pdf_resp.status_code == 200 and is_valid_pdf(pdf_resp.content):
                    dest.write_bytes(pdf_resp.content)
                    return True
    except Exception as e:
        logger.debug(f"Unpaywall failed for {doi}: {e}")
    return False


def try_openalex(session: requests.Session, doi: str, dest: Path) -> bool:
    """Download via OpenAlex repository copies."""
    if not doi:
        return False
    try:
        resp = session.get(f"https://api.openalex.org/works/doi:{doi}", timeout=10)
        if resp.status_code != 200:
            return False
        data = resp.json()
        for loc in data.get("locations") or []:
            if loc.get("is_oa") and loc.get("pdf_url"):
                url = loc["pdf_url"]
                if is_blocked_url(url):
                    continue
                pdf_resp = session.get(url, timeout=30, headers=HEADERS)
                if pdf_resp.status_code == 200 and is_valid_pdf(pdf_resp.content):
                    dest.write_bytes(pdf_resp.content)
                    return True
    except Exception as e:
        logger.debug(f"OpenAlex failed for {doi}: {e}")
    return False


def try_semantic_scholar(session: requests.Session, doi: str, pmid: str, dest: Path) -> bool:
    """Download via Semantic Scholar open access PDFs."""
    if not doi and not pmid:
        return False
    try:
        identifier = f"DOI:{doi}" if doi else f"PMID:{pmid}"
        resp = session.get(
            f"https://api.semanticscholar.org/graph/v1/paper/{identifier}?fields=openAccessPdf",
            timeout=10,
        )
        if resp.status_code == 429:
            time.sleep(5)
            return False
        if resp.status_code != 200:
            return False
        data = resp.json()
        oa = data.get("openAccessPdf")
        if oa and oa.get("url"):
            url = oa["url"]
            if is_blocked_url(url):
                return False
            pdf_resp = session.get(url, timeout=30, headers=HEADERS)
            if pdf_resp.status_code == 200 and is_valid_pdf(pdf_resp.content):
                dest.write_bytes(pdf_resp.content)
                return True
    except Exception as e:
        logger.debug(f"Semantic Scholar failed: {e}")
    return False


def download_from_csv(csv_path: Path, output_dir: Path, limit: int = None) -> None:
    """Download PDFs for papers in the CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)

    # Load CSV
    papers = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            papers.append(row)

    # Skip already downloaded
    existing = {p.stem for p in output_dir.glob("*.pdf")}
    existing_pmids = set()
    for name in existing:
        m = re.search(r"(\d{7,9})", name)
        if m:
            existing_pmids.add(m.group(1))

    to_download = [p for p in papers if p.get("pmid") not in existing_pmids]
    logger.info(f"CSV has {len(papers)} papers, {len(existing_pmids)} already downloaded, {len(to_download)} to try")

    if limit:
        to_download = to_download[:limit]

    downloaded = 0
    needs_access = 0

    for i, row in enumerate(to_download):
        pmid = row.get("pmid", "")
        doi = row.get("doi", "")
        pmc_id = row.get("pmc_id", "")
        title = row.get("title", "")[:60]
        author = re.sub(r"[^A-Za-z]", "", (row.get("first_author", "") or "Unknown").split()[0])
        year = row.get("year", "XXXX")
        fname = f"{year}_{author}_{pmid}.pdf"
        dest = output_dir / fname

        logger.info(f"[{i+1}/{len(to_download)}] {title}...")

        success = False

        # Try each source
        if not success and pmc_id:
            success = try_pmc_ftp(session, pmc_id, dest)
            if success:
                logger.info(f"  ✓ PMC FTP ({dest.stat().st_size // 1024}KB)")
            time.sleep(RATE_DELAY)

        if not success and doi:
            success = try_unpaywall(session, doi, dest)
            if success:
                logger.info(f"  ✓ Unpaywall ({dest.stat().st_size // 1024}KB)")
            time.sleep(RATE_DELAY)

        if not success and doi:
            success = try_openalex(session, doi, dest)
            if success:
                logger.info(f"  ✓ OpenAlex ({dest.stat().st_size // 1024}KB)")
            time.sleep(RATE_DELAY)

        if not success:
            success = try_semantic_scholar(session, doi, pmid, dest)
            if success:
                logger.info(f"  ✓ Semantic Scholar ({dest.stat().st_size // 1024}KB)")
            time.sleep(RATE_DELAY)

        if success:
            downloaded += 1
        else:
            needs_access += 1

        if (i + 1) % 50 == 0:
            logger.info(f"  Progress: {i+1}/{len(to_download)} checked, {downloaded} downloaded")

    print(f"\n{'=' * 50}")
    print(f"DOWNLOAD COMPLETE")
    print(f"{'=' * 50}")
    print(f"Checked:              {len(to_download)}")
    print(f"Downloaded:           {downloaded}")
    print(f"Need institutional:   {needs_access}")
    print(f"Previously had:       {len(existing_pmids)}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    download_from_csv(args.csv, args.output_dir, args.limit)
