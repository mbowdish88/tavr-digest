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
NCBI_TOOL = os.getenv("NCBI_TOOL", "the-valve-wire")
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")

# --- Email SMTP ---
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = [addr.strip() for addr in os.getenv("EMAIL_TO", "").split(",") if addr.strip()]

# --- Beehiiv ---
BEEHIIV_API_KEY = os.getenv("BEEHIIV_API_KEY", "")
BEEHIIV_PUB_ID = os.getenv("BEEHIIV_PUB_ID", "")

# --- Agent Settings ---
PUBMED_MAX_RESULTS = int(os.getenv("PUBMED_MAX_RESULTS", "50"))
NEWS_MAX_RESULTS = int(os.getenv("NEWS_MAX_RESULTS", "30"))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "1"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Search Terms ---
SEARCH_TERMS_AORTIC = [
    "transcatheter aortic valve replacement",
    "TAVR",
    "TAVI",
    "transcatheter aortic valve implantation",
    "Edwards SAPIEN",
    "Medtronic CoreValve",
    "Medtronic Evolut",
    "balloon expandable aortic valve",
    "self expanding aortic valve",
]

SEARCH_TERMS_MITRAL = [
    "MitraClip",
    "PASCAL mitral",
    "transcatheter mitral valve replacement",
    "TMVR",
    "transcatheter mitral valve repair",
    "transcatheter edge-to-edge repair mitral",
    "mitral regurgitation transcatheter",
    "REPAIR-MR trial",
    "PRIMATY trial",
    "Tendyne mitral",
    "Intrepid TMVR",
    "APOLLO mitral trial",
    "Evoque mitral",
    "SAPIEN M3",
    "Cardiovalve",
    "HighLife mitral",
]

SEARCH_TERMS_TRICUSPID = [
    "TriClip",
    "transcatheter tricuspid valve replacement",
    "TTVR",
    "transcatheter tricuspid valve repair",
    "transcatheter edge-to-edge repair tricuspid",
    "tricuspid regurgitation transcatheter",
    "TRILUMINATE trial",
    "CLASP TR trial",
    "Evoque tricuspid",
    "TRISCEND trial",
    "GATE tricuspid",
    "LuX-Valve",
    "NaviGate tricuspid",
]

SEARCH_TERMS_GENERAL = [
    "transcatheter valve therapy",
    "structural heart disease",
    "transcatheter heart valve",
]

SEARCH_TERMS = (
    SEARCH_TERMS_AORTIC
    + SEARCH_TERMS_MITRAL
    + SEARCH_TERMS_TRICUSPID
    + SEARCH_TERMS_GENERAL
)

PUBMED_QUERY = " OR ".join(f'"{term}"' for term in SEARCH_TERMS)

# Separate query for clinical trials only — catches trial publications specifically
PUBMED_CLINICAL_TRIAL_QUERY = (
    f'({PUBMED_QUERY}) AND ("Clinical Trial"[Publication Type] '
    f'OR "Randomized Controlled Trial"[Publication Type] '
    f'OR "Clinical Trial, Phase III"[Publication Type] '
    f'OR "Clinical Trial, Phase IV"[Publication Type])'
)

# --- Surgical vs. Transcatheter Comparison Terms ---
COMPARISON_TERMS = [
    "TAVR versus surgical",
    "TAVR vs SAVR",
    "transcatheter versus surgical aortic valve",
    "MitraClip versus surgery",
    "transcatheter versus surgical mitral",
    "transcatheter versus surgical tricuspid",
    "PARTNER trial",
    "COAPT trial",
    "Evolut Low Risk",
    "REPAIR-MR trial",
    "PRIMATY trial",
    "TRILUMINATE trial",
    "CLASP TR trial",
]

# --- Site-Specific News Sources ---
SITE_SPECIFIC_SEARCHES = [
    {"site": "tctmd.com", "label": "TCTMD"},
    {"site": "cardiovascularbusiness.com", "label": "Cardiovascular Business"},
    {"site": "cms.gov", "label": "CMS", "terms": [
        "TAVR", "TAVI", "transcatheter aortic valve",
        "MitraClip", "transcatheter mitral", "transcatheter tricuspid",
        "structural heart",
    ]},
    {"site": "structuralheartnews.com", "label": "Structural Heart News"},
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

FDA_FILTER_KEYWORDS = [
    "tavr", "tavi", "transcatheter", "aortic valve", "heart valve",
    "edwards", "sapien", "medtronic", "corevalve", "evolut",
    "jena valve", "jenavalve", "j valve",
    "structural heart", "cardiac valve",
    "mitraclip", "pascal", "triclip",
    "mitral", "tricuspid",
    "abbott", "boston scientific", "anteris",
]

# --- Stock Tickers ---
STOCK_TICKERS = {
    "EW": "Edwards Lifesciences",
    "MDT": "Medtronic",
    "ABT": "Abbott",
    "BSX": "Boston Scientific",
    "AVR.AX": "Anteris Technologies",
}
PRIVATE_COMPANIES = [
    "JenaValve Technology",
    "J Valve Technology",
    "Meril Life Sciences",
]

# --- ClinicalTrials.gov ---
CLINICALTRIALS_API_URL = "https://clinicaltrials.gov/api/v2/studies"
CLINICALTRIALS_QUERY = (
    "transcatheter aortic valve replacement OR TAVR OR TAVI "
    "OR MitraClip OR PASCAL OR TMVR OR transcatheter mitral valve "
    "OR transcatheter mitral valve repair OR transcatheter mitral valve replacement "
    "OR TriClip OR TTVR OR transcatheter tricuspid valve "
    "OR transcatheter tricuspid valve repair OR transcatheter tricuspid valve replacement "
    "OR structural heart disease OR edge-to-edge repair "
    "OR Tendyne OR Intrepid OR Evoque OR SAPIEN M3 OR Cardiovalve "
    "OR LuX-Valve OR NaviGate"
)

# Landmark trials to monitor by NCT ID — always fetch these regardless of recency
LANDMARK_TRIALS = {
    # Mitral repair
    "NCT04198870": "REPAIR-MR (MitraClip vs surgery for primary MR)",
    "NCT05051033": "PRIMATY (MitraClip vs medical therapy for secondary MR)",
    "NCT03706833": "COAPT (MitraClip for secondary MR - long-term follow-up)",
    # Mitral replacement
    "NCT04101357": "APOLLO (Tendyne TMVR)",
    "NCT03242642": "Intrepid TMVR Pivotal",
    "NCT05490992": "SAPIEN M3 TMVR Early Feasibility",
    # Tricuspid repair
    "NCT03904147": "TRILUMINATE Pivotal (TriClip for TR)",
    "NCT04097145": "CLASP II TR (PASCAL for TR)",
    # Tricuspid replacement
    "NCT04482062": "TRISCEND II (Evoque tricuspid replacement)",
    "NCT05071768": "GATE Pivotal (NaviGate tricuspid replacement)",
    # Aortic (key ongoing)
    "NCT04728698": "PARTNER 3 Low Risk (5-year follow-up)",
    "NCT02701283": "Evolut Low Risk (long-term follow-up)",
}

# --- Journal RSS Feeds ---
JOURNAL_RSS_FEEDS = [
    {"url": "https://rssfeed.jacc.org/feed/jacc", "label": "JACC"},
    {"url": "https://rssfeed.jacc.org/feed/interventions", "label": "JACC Interventions"},
    {"url": "https://www.ahajournals.org/action/showFeed?type=etoc&feed=rss&jc=circ", "label": "Circulation"},
    {"url": "https://jamanetwork.com/rss/site_191/71.xml", "label": "JAMA Cardiology"},
    {"url": "https://jamanetwork.com/rss/site_7/67.xml", "label": "JAMA"},
    {"url": "https://www.nejm.org/action/showFeed?jc=nejm&type=etoc&feed=rss", "label": "NEJM"},
    {"url": "https://www.jtcvs.org/current.rss", "label": "JTCVS"},
    {"url": "https://www.annalsthoracicsurgery.org/current.rss", "label": "Annals of Thoracic Surgery"},
    {"url": "https://academic.oup.com/ejcts/rss/ahead_of_print", "label": "EJCTS"},
    {"url": "https://academic.oup.com/eurheartj/rss/ahead_of_print", "label": "European Heart Journal"},
    {"url": "https://www.thelancet.com/rssfeed/lancet_current.xml", "label": "Lancet"},
]

# --- Social Media Accounts (for free RSS monitoring) ---
SOCIAL_MEDIA_ACCOUNTS = [
    {"handle": "JACCJournals", "label": "JACC Journals"},
    {"handle": "CircAHA", "label": "Circulation AHA"},
    {"handle": "PCRonline", "label": "PCR Online"},
    {"handle": "STS_CTSurgery", "label": "STS Cardiothoracic Surgery"},
    {"handle": "ACCinTouch", "label": "ACC"},
    {"handle": "EdwardsLifesci", "label": "Edwards Lifesciences"},
    {"handle": "Abornedt", "label": "Medtronic"},
    {"handle": "AbbottNews", "label": "Abbott"},
    {"handle": "BSCCardiology", "label": "Boston Scientific Cardiology"},
    {"handle": "EAPCIPresident", "label": "EAPCI President"},
    {"handle": "Heart_AATS", "label": "AATS"},
    {"handle": "taborneR", "label": "TCTMD"},
]

# --- SEC EDGAR ---
SEC_EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
SEC_EDGAR_COMPANIES = {
    "Edwards Lifesciences": "0001099800",
    "Medtronic": "0001613103",
    "Abbott Laboratories": "0000001800",
    "Boston Scientific": "0000885725",
}
SEC_USER_AGENT = "TheValveWire/1.0 (valve-wire-digest)"

# --- Financial News Search Terms ---
FINANCIAL_NEWS_TERMS = [
    '"structural heart" acquisition',
    '"transcatheter valve" FDA approval',
    '"transcatheter valve" reimbursement',
    "Edwards Lifesciences",
    "Medtronic structural heart",
    "Abbott structural heart",
    "Boston Scientific structural heart",
]

# --- Weekly Summary ---
WEEKLY_DIR = DATA_DIR / "weekly"
WEEKLY_DIR.mkdir(exist_ok=True)
WEEKLY_PUBLISH_DAY = "saturday"

# --- Database ---
DEDUP_DB_PATH = DATA_DIR / "seen_articles.db"
LOG_FILE_PATH = DATA_DIR / "valve_wire.log"
