import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"

DATA_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env", override=True)

# --- Claude API ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# --- NCBI / PubMed ---
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
NCBI_TOOL = os.getenv("NCBI_TOOL", "tavr-digest")
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")

# --- Email SMTP ---
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = [addr.strip() for addr in os.getenv("EMAIL_TO", "").split(",") if addr.strip()]

# --- Agent Settings ---
PUBMED_MAX_RESULTS = int(os.getenv("PUBMED_MAX_RESULTS", "50"))
NEWS_MAX_RESULTS = int(os.getenv("NEWS_MAX_RESULTS", "30"))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "1"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Search Terms ---
SEARCH_TERMS = [
    "transcatheter aortic valve replacement",
    "TAVR",
    "TAVI",
    "transcatheter aortic valve implantation",
    "Edwards SAPIEN",
    "Medtronic CoreValve",
    "balloon expandable aortic valve",
    "self expanding aortic valve",
]

PUBMED_QUERY = " OR ".join(f'"{term}"' for term in SEARCH_TERMS)

# --- Site-Specific News Sources ---
# Google News RSS site-specific searches for key cardiology sites
SITE_SPECIFIC_SEARCHES = [
    {"site": "tctmd.com", "label": "TCTMD"},
    {"site": "cardiovascularbusiness.com", "label": "Cardiovascular Business"},
    {"site": "cms.gov", "label": "CMS", "terms": ["TAVR", "TAVI", "transcatheter aortic valve"]},
]

# --- FDA RSS Feeds ---
FDA_RSS_FEEDS = [
    {
        "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml",
        "label": "FDA Press Releases",
    },
    {
        "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml",
        "label": "FDA MedWatch Safety Alerts",
    },
    {
        "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/recalls/rss.xml",
        "label": "FDA Recalls",
    },
]

# Keywords to filter FDA feed entries for TAVR relevance
FDA_FILTER_KEYWORDS = [
    "tavr", "tavi", "transcatheter", "aortic valve", "heart valve",
    "edwards", "sapien", "medtronic", "corevalve", "evolut",
    "jena valve", "jenavalve", "j valve",
    "structural heart", "cardiac valve",
]

# --- Stock Tickers ---
# Edwards Lifesciences (EW), Medtronic (MDT) are publicly traded
# JenaValve and J Valve are private companies (no ticker)
STOCK_TICKERS = {
    "EW": "Edwards Lifesciences",
    "MDT": "Medtronic",
}
PRIVATE_COMPANIES = ["JenaValve Technology", "J Valve Technology"]

# --- ClinicalTrials.gov ---
CLINICALTRIALS_API_URL = "https://clinicaltrials.gov/api/v2/studies"
CLINICALTRIALS_QUERY = "transcatheter aortic valve replacement OR TAVR OR TAVI"

# --- Database ---
DEDUP_DB_PATH = DATA_DIR / "seen_articles.db"
LOG_FILE_PATH = DATA_DIR / "tavr_digest.log"
