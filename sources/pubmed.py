import logging
import time
import xml.etree.ElementTree as ET

import requests

import config

logger = logging.getLogger(__name__)

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Rate limit: 3 req/s without key, 10 req/s with key
REQUEST_DELAY = 0.1 if config.NCBI_API_KEY else 0.34


def _base_params() -> dict:
    params = {
        "tool": config.NCBI_TOOL,
        "email": config.NCBI_EMAIL,
    }
    if config.NCBI_API_KEY:
        params["api_key"] = config.NCBI_API_KEY
    return params


def _esearch(query: str, max_results: int, reldate: int) -> list[str]:
    params = {
        **_base_params(),
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": "date",
        "datetype": "edat",
        "reldate": reldate,
        "retmode": "xml",
    }

    resp = requests.get(ESEARCH_URL, params=params, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    pmids = [id_elem.text for id_elem in root.findall(".//IdList/Id") if id_elem.text]

    count_elem = root.find(".//Count")
    total = count_elem.text if count_elem is not None else "?"
    logger.info(f"PubMed ESearch: {total} total results, fetching {len(pmids)} PMIDs")

    return pmids


def _efetch(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []

    time.sleep(REQUEST_DELAY)

    params = {
        **_base_params(),
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "abstract",
        "retmode": "xml",
    }

    resp = requests.get(EFETCH_URL, params=params, timeout=60)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    articles = []

    for article_elem in root.findall(".//PubmedArticle"):
        try:
            articles.append(_parse_article(article_elem))
        except Exception as e:
            logger.warning(f"Failed to parse PubMed article: {e}")

    return articles


def _parse_article(elem: ET.Element) -> dict:
    citation = elem.find(".//MedlineCitation")
    article = citation.find(".//Article")

    pmid = citation.findtext("PMID", "")
    title = article.findtext("ArticleTitle", "No title")

    # Abstract may have multiple labeled sections
    abstract_parts = []
    abstract_elem = article.find("Abstract")
    if abstract_elem is not None:
        for text_elem in abstract_elem.findall("AbstractText"):
            label = text_elem.get("Label", "")
            text = "".join(text_elem.itertext()).strip()
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
    abstract = " ".join(abstract_parts) if abstract_parts else "No abstract available."

    # Authors
    authors = []
    for author in article.findall(".//AuthorList/Author"):
        last = author.findtext("LastName", "")
        initials = author.findtext("Initials", "")
        if last:
            authors.append(f"{last} {initials}".strip())
    authors_str = ", ".join(authors[:5])
    if len(authors) > 5:
        authors_str += " et al."

    # Journal
    journal = article.findtext(".//Journal/Title", "")

    # Publication date
    pub_date_elem = article.find(".//Journal/JournalIssue/PubDate")
    pub_date = _parse_pub_date(pub_date_elem)

    # DOI
    doi = ""
    for eloc in article.findall("ELocationID"):
        if eloc.get("EIdType") == "doi":
            doi = eloc.text or ""
            break

    return {
        "id": pmid,
        "title": title,
        "abstract": abstract,
        "authors": authors_str,
        "journal": journal,
        "pub_date": pub_date,
        "doi": doi,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "source": "pubmed",
    }


def _parse_pub_date(elem) -> str:
    if elem is None:
        return ""
    year = elem.findtext("Year", "")
    month = elem.findtext("Month", "")
    day = elem.findtext("Day", "")
    medline_date = elem.findtext("MedlineDate", "")
    if medline_date:
        return medline_date
    parts = [p for p in [year, month, day] if p]
    return " ".join(parts)


def fetch_recent(
    query: str = None,
    days: int = None,
    max_results: int = None,
) -> list[dict]:
    query = query or config.PUBMED_QUERY
    days = days or config.LOOKBACK_DAYS
    max_results = max_results or config.PUBMED_MAX_RESULTS

    logger.info(f"Fetching PubMed articles from last {days} day(s)")
    pmids = _esearch(query, max_results, days)
    articles = _efetch(pmids)
    logger.info(f"PubMed: retrieved {len(articles)} articles")
    return articles
