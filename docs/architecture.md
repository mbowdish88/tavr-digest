# The Valve Wire — Architecture Diagram

## System Overview

```mermaid
graph TB
    subgraph Sources["📡 Data Sources"]
        PUB[PubMed<br/>NCBI eUtils]
        PRE[Preprints<br/>bioRxiv/medRxiv]
        JRN[Journals<br/>11 RSS Feeds]
        NEWS[News<br/>Google News RSS]
        REG[Regulatory<br/>FDA RSS Feeds]
        TRI[Trials<br/>ClinicalTrials.gov]
        STK[Stocks<br/>yfinance]
        SOC[Social<br/>Nitter RSS]
        FIN[Financial<br/>SEC EDGAR]
    end

    subgraph Processing["⚙️ Processing"]
        MAIN[main.py<br/>Orchestrator]
        DEDUP[(SQLite<br/>Dedup DB)]
        CLAUDE_D[Claude API<br/>Digest Generation]
        FALLBACK[Fallback<br/>Plain HTML]
    end

    subgraph Delivery["📬 Delivery"]
        EMAIL[Email<br/>SMTP + Jinja2]
        BEE[Beehiiv<br/>API v2]
        PAGES[GitHub Pages<br/>docs/]
        WEB[website.py<br/>Build JSON + Classify]
        WEB_REPO[thevalvewire-site<br/>Vercel via GitHub API]
    end

    subgraph Weekly["📅 Weekly Pipeline"]
        WCOMP[weekly.py<br/>Compile Mon-Fri]
        CLAUDE_W[Claude API<br/>Weekly Summary]
    end

    subgraph Podcast["🎙️ Podcast Pipeline"]
        SCRIPT[scriptwriter.py<br/>Claude Script]
        TTS[synthesizer.py<br/>OpenAI TTS]
        AUDIO[assembler.py<br/>pydub Assembly]
        TRANS[transcriber.py<br/>Whisper]
        NOTES[show_notes.py<br/>HTML/Markdown]
        PUB_POD[publisher.py<br/>GitHub Releases]
        RSS[RSS Feed<br/>iTunes XML]
    end

    subgraph Ops["🤖 Operations"]
        BOT[bot_server.py<br/>Telegram Bot]
        MON[monitor.py<br/>CI/CD Monitor]
        SUM[daily_summary.py<br/>Status Reports]
    end

    subgraph Knowledge["📚 Knowledge Base"]
        GUIDE[Guidelines<br/>ACC/AHA, ESC]
        PAPERS[Landmark Papers<br/>20+ Studies]
    end

    %% Source → Processing
    PUB & PRE & JRN & NEWS & REG & TRI & STK & SOC & FIN --> MAIN
    MAIN --> DEDUP
    DEDUP --> CLAUDE_D
    CLAUDE_D -. fail .-> FALLBACK
    KNOWLEDGE --> CLAUDE_D

    %% Knowledge injection
    GUIDE & PAPERS --> CLAUDE_D

    %% Daily Delivery
    CLAUDE_D --> EMAIL & BEE & PAGES & WEB
    WEB -->|GitHub API push| WEB_REPO
    FALLBACK --> EMAIL

    %% Weekly
    PAGES -. daily HTML .-> WCOMP
    WCOMP --> CLAUDE_W
    CLAUDE_W --> EMAIL
    CLAUDE_W --> PAGES

    %% Podcast
    CLAUDE_W -. weekly content .-> SCRIPT
    SCRIPT --> TTS
    TTS --> AUDIO
    AUDIO --> TRANS
    AUDIO --> PUB_POD
    TRANS --> NOTES
    PUB_POD --> RSS

    %% Ops
    BOT -. triggers .-> MAIN
    MON -. monitors .-> MAIN
    SUM -. reports .-> BOT

    %% Styling
    classDef source fill:#e1f5fe,stroke:#0288d1
    classDef process fill:#fff3e0,stroke:#f57c00
    classDef deliver fill:#e8f5e9,stroke:#388e3c
    classDef podcast fill:#f3e5f5,stroke:#7b1fa2
    classDef ops fill:#fce4ec,stroke:#c62828
    classDef knowledge fill:#fffde7,stroke:#f9a825

    class PUB,PRE,JRN,NEWS,REG,TRI,STK,SOC,FIN source
    class MAIN,DEDUP,CLAUDE_D,FALLBACK process
    class EMAIL,BEE,PAGES,WEB,WEB_REPO deliver
    class SCRIPT,TTS,AUDIO,TRANS,NOTES,PUB_POD,RSS podcast
    class BOT,MON,SUM ops
    class GUIDE,PAPERS knowledge
```

## Daily Pipeline Sequence

```mermaid
sequenceDiagram
    participant GHA as GitHub Actions
    participant Main as main.py
    participant Src as Sources (9)
    participant DB as SQLite Dedup
    participant AI as Claude API
    participant Del as Delivery

    GHA->>Main: Cron 6 AM CT
    
    loop Each Source
        Main->>Src: Fetch articles
        Src-->>Main: Article list (or error, continue)
    end

    Main->>DB: Filter seen articles
    DB-->>Main: New articles only

    alt No new articles
        Main->>Main: Skip digest, exit
    end

    Main->>AI: Generate digest (attempt 1)
    alt API fails
        Main->>AI: Retry after 30s (attempt 2)
        alt Still fails
            Main->>Main: build_fallback_digest()
        end
    end

    par Publish
        Main->>Del: Email (SMTP)
        Main->>Del: Beehiiv (API)
        Main->>Del: GitHub Pages (docs/)
        Main->>Del: Vercel (JSON)
    end

    alt Email succeeded
        Main->>DB: Mark articles seen
    end

    Main->>Main: Save digest for weekly
```

## Podcast Generation Flow

```mermaid
flowchart LR
    A[Weekly<br/>Content] --> B[Claude<br/>Script]
    B --> C{OpenAI TTS}
    C --> D[Nolan<br/>fable voice]
    C --> E[Claire<br/>nova voice]
    D & E --> F[Audio<br/>Processing]
    F --> G[pydub<br/>Assembly]
    
    H[Intro WAV] --> G
    I[Outro WAV] --> G
    J[Transitions] --> G
    K[Background] --> G
    
    G --> L[Final MP3]
    L --> M[Whisper<br/>Transcribe]
    L --> N[GitHub<br/>Release]
    M --> O[Show Notes]
    N --> P[RSS Feed]
```

## Module Dependency Map

```mermaid
graph LR
    subgraph Entry
        MAIN[main.py]
    end

    subgraph sources
        pubmed
        preprints
        journals
        news
        regulatory
        trials
        stocks
        social
        financial
    end

    subgraph processing
        dedup
        summarizer
        weekly
    end

    subgraph delivery
        emailer
        beehiiv
        site
        website
    end

    subgraph podcast
        scriptwriter
        synthesizer
        audio_processing
        assembler
        transcriber
        show_notes
        publisher
    end

    CONFIG[config.py]

    MAIN --> sources
    MAIN --> processing
    MAIN --> delivery
    MAIN --> podcast
    sources --> CONFIG
    processing --> CONFIG
    delivery --> CONFIG
    podcast --> CONFIG

    synthesizer --> audio_processing
    assembler --> audio_processing
```

## Vercel Website Data Flow

The Vercel website lives in a separate repo (`mbowdish88/thevalvewire-site`) and receives structured JSON from `delivery/website.py` via the GitHub API.

```mermaid
flowchart TB
    subgraph tavr-digest["tavr-digest repo"]
        MAIN[main.py] --> BUILD[website.py<br/>build_website_data]
        
        BUILD --> CLASS[Classify Articles<br/>aortic/mitral/tricuspid<br/>surgical/trials/regulatory/financial]
        BUILD --> OG[Fetch OG Images<br/>first 20 articles]
        BUILD --> SUMMARY[Extract Executive<br/>Summary + Key Points]
        BUILD --> STOCKS[Format Stock Data<br/>EW MDT ABT BSX AVR.AX]
        BUILD --> POD_EP[Load Podcast<br/>Episodes]
    end

    subgraph push["GitHub API Push"]
        CLASS & OG & SUMMARY & STOCKS & POD_EP --> JSON[Structured JSON]
        JSON --> MERGE{Sparse today?<br/>< 5 articles}
        MERGE -->|yes| FILL[Fill empty sections<br/>from previous day]
        MERGE -->|no| PUSH[Push to repo]
        FILL --> PUSH
    end

    subgraph website["thevalvewire-site repo (Vercel)"]
        PUSH --> LATEST[public/data/<br/>latest.json]
        PUSH --> ARCHIVE[public/data/digests/<br/>YYYY-MM-DD.json]
        LATEST --> VERCEL[Vercel Deployment]
    end

    style tavr-digest fill:#fff3e0,stroke:#f57c00
    style push fill:#e1f5fe,stroke:#0288d1
    style website fill:#e8f5e9,stroke:#388e3c
```

### Website JSON Structure

```
latest.json
├── date                    # ISO date
├── executive_summary       # Extracted from Claude digest HTML
├── key_points[]            # Up to 5 bullet points
├── sections
│   ├── aortic              # TAVR/TAVI articles
│   ├── mitral              # MitraClip, PASCAL, TMVR
│   ├── tricuspid           # TriClip, TTVR
│   ├── surgical            # Surgical vs transcatheter
│   ├── trials              # ClinicalTrials.gov updates
│   ├── regulatory          # FDA alerts, approvals
│   └── financial           # SEC filings, M&A
│       └── articles[]
│           ├── id, type, title, source
│           ├── url, date, abstract
│           ├── authors, image_url (OG)
│           └── nct_id, phase, status (trials only)
├── stocks
│   └── {ticker}
│       ├── price, change, change_pct
│       ├── high_6m, low_6m, change_6m
│       ├── market_cap, pe_ratio
│       ├── target_price, recommendation
│       └── price_history{}
└── podcast
    ├── latest_episode
    └── all_episodes[]
```

## Infrastructure

```mermaid
graph TB
    subgraph "GitHub Actions (CI/CD)"
        D[daily-digest.yml<br/>Daily 6 AM CT]
        W[weekly-digest.yml<br/>Saturday]
        P[weekly-podcast.yml<br/>After weekly]
        M[monitor.yml<br/>On completion]
        S[daily-summary.yml<br/>Morning]
    end

    subgraph "Railway"
        BOT[bot_server.py<br/>Always-on]
    end

    subgraph "External Services"
        CLAUDE[Anthropic Claude]
        OAI[OpenAI TTS/Whisper]
        SMTP_SVC[SMTP Server]
        BH[Beehiiv]
        TG[Telegram]
        GH_REL[GitHub Releases]
        GH_API[GitHub API]
    end

    subgraph "Publishing"
        GP[GitHub Pages<br/>thevalvewire.com/docs]
        VER_REPO[thevalvewire-site repo]
        VER[Vercel Deployment]
    end

    D --> CLAUDE & SMTP_SVC & BH & GP
    D -->|website.py| GH_API
    GH_API -->|push JSON| VER_REPO
    VER_REPO --> VER
    W --> CLAUDE & SMTP_SVC & GP
    W -.->|triggers| P
    P --> CLAUDE & OAI & GH_REL
    M --> CLAUDE & TG
    S --> TG
    BOT --> TG & CLAUDE
```
