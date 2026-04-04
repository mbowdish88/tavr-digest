#!/usr/bin/env python3
"""
Standalone PubMed paper search and download script for structural heart disease.

============================================================================
This script downloads open-access papers WITHOUT institutional access.

It cascades through 9 free sources in order:
  1. PMC FTP/OA service — tar.gz packages via HTTPS, no bot blocking
  2. Europe PMC — often serves PDFs more freely than NIH PMC
  3. Unpaywall API — finds repository/preprint PDFs (skips publisher URLs)
  4. OpenAlex API — finds repository PDFs from European university repos
  5. Semantic Scholar — open access PDF links (skips blocked publishers)
  6. CORE.ac.uk — institutional repository copies
  7. Crossref — publisher full-text links
  8. PMC web — direct PDF from PubMed Central (may be blocked)
  9. DOI direct — follows DOI redirect (works best with institutional access)

From a HOME IP, sources 1-5 are the most productive. Sources 3-5 specifically
filter for institutional repository URLs (universities, preprint servers) and
skip publisher domains (NEJM, JAMA, JACC, Lancet, etc.) that block automated
downloads. Expect ~20-25% success rate from home (~2,500 of 10,500 papers).
The remaining ~75% require Cedars VPN or on-campus access.

Papers that can't be downloaded from any source go to
needs_institutional_access.txt for manual download at Cedars.

After downloading, copy the PDFs back to:
  ~/projects/tavr-digest/knowledge/papers/inbox/
Then run: python -m knowledge.indexer
The indexer will catalog, rename, and integrate them into the knowledge base.

Optional env vars:
  NCBI_API_KEY     — faster NCBI rate limits (10 req/s vs 3 req/s)
  CORE_API_KEY     — higher CORE.ac.uk rate limits
  CONTACT_EMAIL    — polite email for API usage (default: thevalvewire@gmail.com)
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
# PDF download — multi-source cascade for open-access papers
# ---------------------------------------------------------------------------

# Contact email for polite API usage (Unpaywall requires it)
_CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "thevalvewire@gmail.com")

# Shared headers for web requests
_HEADERS = {
    "User-Agent": (
        "TheValveWire/1.0 (academic newsletter; mailto:{email}) "
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    ).format(email=_CONTACT_EMAIL),
}


def _is_valid_pdf(data: bytes) -> bool:
    """Check if data starts with a PDF magic number."""
    return data[:5] == b"%PDF-"


def _save_if_pdf(data: bytes, output_path: Path) -> bool:
    """Save data to output_path if it looks like a valid PDF."""
    if _is_valid_pdf(data) and len(data) > 1000:
        output_path.write_bytes(data)
        return True
    return False


# --- Source 1: PMC FTP (tar.gz packages — no web server blocking) ----------

def download_pdf_from_pmc_ftp(pmc_id: str, output_path: Path) -> bool:
    """Download PDF from PMC FTP archive via HTTPS OA file list.

    The PMC OA file list maps PMC IDs to tar.gz packages on the FTP server.
    We use the HTTPS mirror (no need for actual FTP client).
    """
    import tarfile
    import io

    # Strip "PMC" prefix if present for the numeric ID
    pmc_num = pmc_id.replace("PMC", "")

    # Use the PMC OA web service to get the package URL
    oa_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC{pmc_num}"
    try:
        _throttle()
        resp = requests.get(oa_url, timeout=30, headers=_HEADERS)
        if resp.status_code != 200:
            return False

        # Parse the XML response to find the tgz link
        root = ElementTree.fromstring(resp.content)

        def _ftp_to_https(url: str) -> str:
            """Convert ftp://ftp.ncbi.nlm.nih.gov/ URLs to https:// mirror."""
            if url.startswith("ftp://ftp.ncbi.nlm.nih.gov/"):
                return url.replace("ftp://ftp.ncbi.nlm.nih.gov/", "https://ftp.ncbi.nlm.nih.gov/", 1)
            return url

        # Look for PDF link first, then tgz
        for record in root.findall(".//record"):
            for link in record.findall("link"):
                fmt = link.get("format", "")
                href = _ftp_to_https(link.get("href", ""))
                if fmt == "pdf" and href:
                    # Direct PDF link from OA service
                    _throttle()
                    pdf_resp = requests.get(href, timeout=120, headers=_HEADERS)
                    if pdf_resp.status_code == 200 and _save_if_pdf(pdf_resp.content, output_path):
                        log.debug(f"  PMC FTP (direct PDF): success for {pmc_id}")
                        return True

            for link in record.findall("link"):
                fmt = link.get("format", "")
                href = _ftp_to_https(link.get("href", ""))
                if fmt == "tgz" and href:
                    # Download tar.gz and extract PDF
                    _throttle()
                    tgz_resp = requests.get(href, timeout=180, headers=_HEADERS, stream=True)
                    if tgz_resp.status_code != 200:
                        continue
                    tgz_data = tgz_resp.content
                    try:
                        with tarfile.open(fileobj=io.BytesIO(tgz_data), mode="r:gz") as tar:
                            for member in tar.getmembers():
                                if member.name.lower().endswith(".pdf"):
                                    f = tar.extractfile(member)
                                    if f:
                                        pdf_data = f.read()
                                        if _save_if_pdf(pdf_data, output_path):
                                            log.debug(f"  PMC FTP (tgz): success for {pmc_id}")
                                            return True
                    except (tarfile.TarError, IOError) as e:
                        log.debug(f"  PMC FTP tar extraction failed for {pmc_id}: {e}")
    except requests.RequestException as e:
        log.debug(f"  PMC FTP failed for {pmc_id}: {e}")
    return False


# --- Source 2: Europe PMC --------------------------------------------------

def download_pdf_from_europepmc(pmc_id: str, pmid: str, output_path: Path) -> bool:
    """Download PDF from Europe PMC — often serves PDFs more freely than NIH PMC."""
    urls_to_try = []
    if pmc_id:
        pmc_num = pmc_id.replace("PMC", "")
        urls_to_try.append(
            f"https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC{pmc_num}&blobtype=pdf"
        )
    if pmid:
        urls_to_try.append(
            f"https://europepmc.org/article/med/{pmid}?format=pdf"
        )

    for url in urls_to_try:
        try:
            _throttle()
            resp = requests.get(url, timeout=60, headers=_HEADERS, allow_redirects=True)
            if resp.status_code == 200 and _save_if_pdf(resp.content, output_path):
                log.debug(f"  Europe PMC: success")
                return True
        except requests.RequestException as e:
            log.debug(f"  Europe PMC failed: {e}")
    return False


# Publisher domains that block automated downloads from non-institutional IPs
_PUBLISHER_DOMAINS = {
    "nejm.org", "jamanetwork.com", "jacc.org", "thelancet.com",
    "ahajournals.org", "elsevier.com", "linkinghub.elsevier.com",
    "springer.com", "nature.com", "doi.org", "wiley.com",
    "oxfordjournals.org", "academic.oup.com", "bmj.com",
    "sciencedirect.com", "karger.com", "wolterskluwer.com",
    "lww.com", "annals.org",
}

# PMC domains that return HTML instead of PDFs from home IPs
_PMC_DOMAINS = {
    "pmc.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov/pmc",
}


def _is_blocked_url(url: str) -> bool:
    """Check if a URL is on a publisher or PMC domain that blocks home downloads."""
    url_lower = url.lower()
    for domain in _PUBLISHER_DOMAINS | _PMC_DOMAINS:
        if domain in url_lower:
            return True
    return False


# --- Source 3: Unpaywall API (repository copies only) ----------------------

def download_pdf_from_unpaywall(doi: str, output_path: Path) -> bool:
    """Use Unpaywall API to find OA PDF from institutional repositories.

    Only tries repository/preprint URLs — publisher and PMC URLs are skipped
    because they block automated downloads from non-institutional IPs.
    """
    if not doi:
        return False
    url = f"https://api.unpaywall.org/v2/{doi}?email={_CONTACT_EMAIL}"
    try:
        _throttle()
        resp = requests.get(url, timeout=30, headers=_HEADERS)
        if resp.status_code != 200:
            return False
        data = resp.json()

        # Collect repository PDF URLs only (skip publisher and PMC)
        pdf_urls = []
        for loc in data.get("oa_locations", []):
            pdf_url = loc.get("url_for_pdf", "")
            if pdf_url and not _is_blocked_url(pdf_url):
                pdf_urls.append(pdf_url)

        for pdf_url in pdf_urls[:5]:
            try:
                _throttle()
                pdf_resp = requests.get(
                    pdf_url, timeout=60, headers=_HEADERS, allow_redirects=True,
                )
                if pdf_resp.status_code == 200 and _save_if_pdf(pdf_resp.content, output_path):
                    log.debug(f"  Unpaywall (repo): success from {pdf_url[:80]}")
                    return True
            except requests.RequestException:
                continue
    except (requests.RequestException, ValueError) as e:
        log.debug(f"  Unpaywall failed for {doi}: {e}")
    return False


# --- Source 4: OpenAlex (repository copies) --------------------------------

def download_pdf_from_openalex(doi: str, output_path: Path) -> bool:
    """Use OpenAlex API to find OA PDF from institutional repositories.

    OpenAlex often surfaces repository PDFs from European universities
    (Copenhagen, Erasmus, Amsterdam UMC, etc.) that Unpaywall misses.
    """
    if not doi:
        return False
    url = f"https://api.openalex.org/works/doi:{doi}"
    headers = {**_HEADERS, "User-Agent": f"mailto:{_CONTACT_EMAIL}"}
    try:
        _throttle()
        resp = requests.get(url, timeout=30, headers=headers)
        if resp.status_code != 200:
            return False
        data = resp.json()

        # Collect repository PDF URLs only
        pdf_urls = []
        for loc in data.get("locations", []):
            pdf_url = loc.get("pdf_url")
            if not pdf_url:
                continue
            src = loc.get("source", {}) or {}
            # Only try repository sources, skip publishers and PMC
            if src.get("type") == "repository" and not _is_blocked_url(pdf_url):
                pdf_urls.append(pdf_url)

        for pdf_url in pdf_urls[:5]:
            try:
                _throttle()
                pdf_resp = requests.get(
                    pdf_url, timeout=60, headers=_HEADERS, allow_redirects=True,
                )
                if pdf_resp.status_code == 200 and _save_if_pdf(pdf_resp.content, output_path):
                    log.debug(f"  OpenAlex (repo): success from {pdf_url[:80]}")
                    return True
            except requests.RequestException:
                continue
    except (requests.RequestException, ValueError) as e:
        log.debug(f"  OpenAlex failed for {doi}: {e}")
    return False


# --- Source 5: Semantic Scholar (repository copies only) -------------------

def download_pdf_from_semantic_scholar(pmid: str, doi: str, output_path: Path) -> bool:
    """Use Semantic Scholar API to find open access PDF.

    Skips publisher URLs that are known to block non-institutional IPs.
    """
    # Try PMID first, then DOI
    identifiers = []
    if pmid:
        identifiers.append(f"PMID:{pmid}")
    if doi:
        identifiers.append(f"DOI:{doi}")

    for ident in identifiers:
        url = f"https://api.semanticscholar.org/graph/v1/paper/{ident}?fields=openAccessPdf"
        try:
            _throttle()
            resp = requests.get(url, timeout=30, headers=_HEADERS)
            if resp.status_code == 200:
                data = resp.json()
                oa_pdf = data.get("openAccessPdf")
                if oa_pdf and oa_pdf.get("url"):
                    pdf_url = oa_pdf["url"]
                    if _is_blocked_url(pdf_url):
                        log.debug(f"  Semantic Scholar: skipping blocked URL {pdf_url[:80]}")
                        continue
                    _throttle()
                    pdf_resp = requests.get(
                        pdf_url, timeout=60, headers=_HEADERS, allow_redirects=True,
                    )
                    if pdf_resp.status_code == 200 and _save_if_pdf(pdf_resp.content, output_path):
                        log.debug(f"  Semantic Scholar: success from {pdf_url[:80]}")
                        return True
            elif resp.status_code == 429:
                # Rate limited — back off
                time.sleep(5)
        except (requests.RequestException, ValueError) as e:
            log.debug(f"  Semantic Scholar failed for {ident}: {e}")
    return False


# --- Source 6: CORE.ac.uk -------------------------------------------------

def download_pdf_from_core(doi: str, output_path: Path) -> bool:
    """Search CORE.ac.uk for repository copies of the paper."""
    if not doi:
        return False
    core_api_key = os.environ.get("CORE_API_KEY", "")

    # CORE search by DOI
    url = f"https://api.core.ac.uk/v3/search/works?q=doi%3A%22{doi}%22&limit=3"
    headers = {**_HEADERS}
    if core_api_key:
        headers["Authorization"] = f"Bearer {core_api_key}"
    try:
        _throttle()
        resp = requests.get(url, timeout=30, headers=headers)
        if resp.status_code != 200:
            return False
        data = resp.json()
        results = data.get("results", [])

        for result in results:
            # Check for downloadUrl
            download_url = result.get("downloadUrl", "")
            if download_url:
                try:
                    _throttle()
                    pdf_resp = requests.get(
                        download_url, timeout=60, headers=_HEADERS, allow_redirects=True,
                    )
                    if pdf_resp.status_code == 200 and _save_if_pdf(pdf_resp.content, output_path):
                        log.debug(f"  CORE: success from {download_url[:80]}")
                        return True
                except requests.RequestException:
                    continue

            # Check sourceFulltextUrls
            for furl in result.get("sourceFulltextUrls", []):
                if furl:
                    try:
                        _throttle()
                        pdf_resp = requests.get(
                            furl, timeout=60, headers=_HEADERS, allow_redirects=True,
                        )
                        if pdf_resp.status_code == 200 and _save_if_pdf(pdf_resp.content, output_path):
                            log.debug(f"  CORE: success from {furl[:80]}")
                            return True
                    except requests.RequestException:
                        continue
    except (requests.RequestException, ValueError) as e:
        log.debug(f"  CORE failed for {doi}: {e}")
    return False


# --- Source 7: Crossref full-text links ------------------------------------

def download_pdf_from_crossref(doi: str, output_path: Path) -> bool:
    """Use Crossref API to find full-text PDF links."""
    if not doi:
        return False
    url = f"https://api.crossref.org/works/{doi}"
    headers = {
        **_HEADERS,
        "User-Agent": f"TheValveWire/1.0 (mailto:{_CONTACT_EMAIL})",
    }
    try:
        _throttle()
        resp = requests.get(url, timeout=30, headers=headers)
        if resp.status_code != 200:
            return False
        data = resp.json()
        message = data.get("message", {})

        # Look for PDF links in the "link" array
        pdf_urls = []
        for link in message.get("link", []):
            content_type = link.get("content-type", "")
            url_val = link.get("URL", "")
            if "pdf" in content_type.lower() and url_val:
                pdf_urls.append(url_val)

        for pdf_url in pdf_urls[:3]:
            try:
                _throttle()
                pdf_resp = requests.get(
                    pdf_url, timeout=60, headers=_HEADERS, allow_redirects=True,
                )
                if pdf_resp.status_code == 200 and _save_if_pdf(pdf_resp.content, output_path):
                    log.debug(f"  Crossref: success from {pdf_url[:80]}")
                    return True
            except requests.RequestException:
                continue
    except (requests.RequestException, ValueError) as e:
        log.debug(f"  Crossref failed for {doi}: {e}")
    return False


# --- Source 8: PMC web (original, kept as fallback) ------------------------

def download_pdf_from_pmc(pmc_id: str, output_path: Path) -> bool:
    """Attempt to download a PDF from PubMed Central web server."""
    url = f"{PMC_PDF_BASE}/{pmc_id}/pdf/"
    try:
        _throttle()
        resp = requests.get(url, timeout=60, allow_redirects=True, headers=_HEADERS)
        if resp.status_code == 200 and _save_if_pdf(resp.content, output_path):
            return True
        # Try alternate URL pattern
        url_alt = f"{PMC_PDF_BASE}/{pmc_id}/pdf/main.pdf"
        _throttle()
        resp = requests.get(url_alt, timeout=60, allow_redirects=True, headers=_HEADERS)
        if resp.status_code == 200 and _save_if_pdf(resp.content, output_path):
            return True
    except requests.RequestException as e:
        log.debug(f"PMC web download failed for {pmc_id}: {e}")
    return False


# --- Source 9: DOI direct (original, kept as fallback) ---------------------

def download_pdf_from_doi(doi: str, output_path: Path) -> bool:
    """Attempt to download a PDF via DOI redirect (works best with institutional access)."""
    if not doi:
        return False
    url = f"https://doi.org/{doi}"
    headers = {
        **_HEADERS,
        "Accept": "application/pdf",
    }
    try:
        _throttle()
        resp = requests.get(
            url, headers=headers, timeout=60, allow_redirects=True, stream=True
        )
        content_type = resp.headers.get("content-type", "")
        if resp.status_code == 200 and "pdf" in content_type.lower():
            if _save_if_pdf(resp.content, output_path):
                return True
    except requests.RequestException as e:
        log.debug(f"DOI download failed for {doi}: {e}")
    return False


# --- Download orchestrator -------------------------------------------------

# Download source cascade — ordered by reliability for home IP (no institutional access)
#
# Sources 1-5 find repository PDFs from institutional repositories (universities,
# preprint servers) which are freely downloadable from any IP.
# Sources 6-9 are fallbacks that mostly work only with institutional access.
DOWNLOAD_SOURCES = [
    ("PMC FTP/OA",       lambda art, out: download_pdf_from_pmc_ftp(art.get("pmc_id", ""), out)),
    ("Europe PMC",       lambda art, out: download_pdf_from_europepmc(art.get("pmc_id", ""), art.get("pmid", ""), out)),
    ("Unpaywall",        lambda art, out: download_pdf_from_unpaywall(art.get("doi", ""), out)),
    ("OpenAlex",         lambda art, out: download_pdf_from_openalex(art.get("doi", ""), out)),
    ("Semantic Scholar", lambda art, out: download_pdf_from_semantic_scholar(art.get("pmid", ""), art.get("doi", ""), out)),
    ("CORE",             lambda art, out: download_pdf_from_core(art.get("doi", ""), out)),
    ("Crossref",         lambda art, out: download_pdf_from_crossref(art.get("doi", ""), out)),
    ("PMC web",          lambda art, out: download_pdf_from_pmc(art.get("pmc_id", ""), out) if art.get("pmc_id") else False),
    ("DOI direct",       lambda art, out: download_pdf_from_doi(art.get("doi", ""), out)),
]


def _try_download_cascade(art: Dict, output_path: Path) -> Optional[str]:
    """Try each download source in order. Returns the source name on success, None on failure."""
    for source_name, download_fn in DOWNLOAD_SOURCES:
        try:
            if download_fn(art, output_path):
                return source_name
        except Exception as e:
            log.debug(f"  {source_name} raised unexpected error: {e}")
    return None


def download_papers(
    articles: Dict[str, Dict], output_dir: Path, dry_run: bool = False,
    limit: Optional[int] = None,
) -> Tuple[int, int, List[Dict]]:
    """Download available PDFs using multi-source cascade.

    Tries 9 sources in order: PMC FTP/OA, Europe PMC, Unpaywall, OpenAlex,
    Semantic Scholar, CORE, Crossref, PMC web, DOI direct.

    Returns (downloaded_count, failed_count, needs_access_list).
    """
    downloaded = 0
    failed = 0
    needs_access = []
    source_stats: Dict[str, int] = {}

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

        log.info(f"[{i}/{total}] Trying to download: {art.get('title', '')[:60]}...")
        source = _try_download_cascade(art, output_path)

        if source:
            art["pdf_downloaded"] = True
            art["pdf_filename"] = filename
            art["download_source"] = source
            downloaded += 1
            source_stats[source] = source_stats.get(source, 0) + 1
            log.info(f"  -> Downloaded via {source}")
        else:
            failed += 1
            needs_access.append(art)

        if i % 25 == 0:
            log.info(f"  Progress: {i}/{total} checked, {downloaded} downloaded, {failed} failed")

    # Print source breakdown
    if source_stats:
        log.info("Download source breakdown:")
        for src, count in sorted(source_stats.items(), key=lambda x: -x[1]):
            log.info(f"  {src}: {count} papers")

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
        "pdf_filename", "download_source", "pubmed_url", "doi_url", "search_source_type",
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

    # Download source breakdown
    by_source: Dict[str, int] = {}
    for art in articles.values():
        src = art.get("download_source")
        if src:
            by_source[src] = by_source.get(src, 0) + 1

    print("\n" + "=" * 60)
    print("PAPER SEARCH SUMMARY")
    print("=" * 60)
    print(f"Total unique papers found:  {total}")
    print(f"With PMC ID:                {with_pmc}")
    print(f"PDFs downloaded:            {downloaded}")
    print(f"Need institutional access:  {failed}")
    print()
    if by_source:
        print("Downloads by source:")
        for src, c in sorted(by_source.items(), key=lambda x: -x[1]):
            print(f"  {src}: {c}")
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
