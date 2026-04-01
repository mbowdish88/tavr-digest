"""Generate architecture diagrams as PNG files for PowerPoint/documents."""

import subprocess
import textwrap
from pathlib import Path

OUT = Path("/home/user/tavr-digest/docs/diagrams")
OUT.mkdir(parents=True, exist_ok=True)

# Shared styling
GRAPH_ATTRS = {
    "fontname": "Helvetica",
    "fontsize": "11",
    "bgcolor": "white",
    "pad": "0.5",
    "dpi": "200",
    "rankdir": "TB",
}
NODE_ATTRS = 'fontname="Helvetica" fontsize="10" style="filled,rounded" shape="box" penwidth="1.5"'
EDGE_ATTRS = 'fontname="Helvetica" fontsize="9" penwidth="1.2"'

# Color palette
SOURCE_COLOR = "#DBEAFE"      # light blue
SOURCE_BORDER = "#2563EB"
PROCESS_COLOR = "#FEF3C7"     # light amber
PROCESS_BORDER = "#D97706"
DELIVER_COLOR = "#D1FAE5"     # light green
DELIVER_BORDER = "#059669"
PODCAST_COLOR = "#EDE9FE"     # light purple
PODCAST_BORDER = "#7C3AED"
OPS_COLOR = "#FCE7F3"         # light pink
OPS_BORDER = "#DB2777"
KNOWLEDGE_COLOR = "#FEF9C3"   # light yellow
KNOWLEDGE_BORDER = "#CA8A04"
WEBSITE_COLOR = "#CFFAFE"     # light cyan
WEBSITE_BORDER = "#0891B2"


def render(name: str, dot: str):
    """Render a dot string to PNG and SVG."""
    dot_file = OUT / f"{name}.dot"
    dot_file.write_text(dot)
    for fmt in ("png", "svg"):
        out_file = OUT / f"{name}.{fmt}"
        subprocess.run(
            ["dot", f"-T{fmt}", "-Gdpi=200", str(dot_file), "-o", str(out_file)],
            check=True,
        )
    dot_file.unlink()
    print(f"  -> {OUT / name}.png + .svg")


# ──────────────────────────────────────────────
# 1. SYSTEM OVERVIEW
# ──────────────────────────────────────────────
print("1. System Overview...")
render("01_system_overview", textwrap.dedent(f"""\
digraph system_overview {{
    graph [fontname="Helvetica" fontsize="12" bgcolor="white" pad="0.6"
           rankdir="TB" label="The Valve Wire — System Overview" labelloc="t"
           labelfontsize="16" labelfontcolor="#1E293B" nodesep="0.4" ranksep="0.6"]
    node [{NODE_ATTRS}]
    edge [{EDGE_ATTRS}]

    // Sources
    subgraph cluster_sources {{
        label="Data Sources" style="filled,rounded" fillcolor="#F0F9FF"
        color="{SOURCE_BORDER}" fontcolor="{SOURCE_BORDER}" fontsize="12"
        pubmed   [label="PubMed\\nNCBI eUtils"     fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
        preprints[label="Preprints\\nbioRxiv/medRxiv" fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
        journals [label="Journals\\n11 RSS Feeds"   fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
        news     [label="News\\nGoogle News RSS"    fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
        regulatory[label="Regulatory\\nFDA RSS"     fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
        trials   [label="Trials\\nClinicalTrials.gov" fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
        stocks   [label="Stocks\\nyfinance"         fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
        social   [label="Social\\nNitter RSS"       fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
        financial[label="Financial\\nSEC EDGAR"     fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
    }}

    // Processing
    subgraph cluster_processing {{
        label="Processing" style="filled,rounded" fillcolor="#FFFBEB"
        color="{PROCESS_BORDER}" fontcolor="{PROCESS_BORDER}" fontsize="12"
        main    [label="main.py\\nOrchestrator"     fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]
        dedup   [label="SQLite\\nDedup DB"          fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}" shape="cylinder"]
        claude  [label="Claude API\\nDigest Gen"    fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]
        fallback[label="Fallback\\nPlain HTML"      fillcolor="#FEE2E2" color="#DC2626" style="filled,rounded,dashed"]
    }}

    // Knowledge
    subgraph cluster_knowledge {{
        label="Knowledge Base" style="filled,rounded" fillcolor="#FEFCE8"
        color="{KNOWLEDGE_BORDER}" fontcolor="{KNOWLEDGE_BORDER}" fontsize="12"
        guidelines[label="Guidelines\\nACC/AHA, ESC" fillcolor="{KNOWLEDGE_COLOR}" color="{KNOWLEDGE_BORDER}"]
        papers    [label="Landmark Papers\\n20+ Studies" fillcolor="{KNOWLEDGE_COLOR}" color="{KNOWLEDGE_BORDER}"]
    }}

    // Delivery
    subgraph cluster_delivery {{
        label="Delivery" style="filled,rounded" fillcolor="#ECFDF5"
        color="{DELIVER_BORDER}" fontcolor="{DELIVER_BORDER}" fontsize="12"
        email  [label="Email\\nSMTP + Jinja2"     fillcolor="{DELIVER_COLOR}" color="{DELIVER_BORDER}"]
        beehiiv[label="Beehiiv\\nAPI v2"           fillcolor="{DELIVER_COLOR}" color="{DELIVER_BORDER}"]
        pages  [label="GitHub Pages\\ndocs/"       fillcolor="{DELIVER_COLOR}" color="{DELIVER_BORDER}"]
        webpy  [label="website.py\\nBuild JSON"    fillcolor="{WEBSITE_COLOR}" color="{WEBSITE_BORDER}"]
    }}

    // Website
    subgraph cluster_website {{
        label="Vercel Website" style="filled,rounded" fillcolor="#ECFEFF"
        color="{WEBSITE_BORDER}" fontcolor="{WEBSITE_BORDER}" fontsize="12"
        webrepo[label="thevalvewire-site\\nGitHub Repo" fillcolor="{WEBSITE_COLOR}" color="{WEBSITE_BORDER}"]
        vercel [label="Vercel\\nDeployment"        fillcolor="{WEBSITE_COLOR}" color="{WEBSITE_BORDER}"]
    }}

    // Weekly
    subgraph cluster_weekly {{
        label="Weekly Pipeline" style="filled,rounded" fillcolor="#F5F3FF"
        color="{PODCAST_BORDER}" fontcolor="{PODCAST_BORDER}" fontsize="12"
        weekly_comp  [label="weekly.py\\nCompile Mon-Fri" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]
        weekly_claude[label="Claude API\\nWeekly Summary" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]
    }}

    // Podcast
    subgraph cluster_podcast {{
        label="Podcast Pipeline" style="filled,rounded" fillcolor="#F5F3FF"
        color="{PODCAST_BORDER}" fontcolor="{PODCAST_BORDER}" fontsize="12"
        script [label="Claude\\nScript Gen"     fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]
        tts    [label="OpenAI TTS\\nNolan + Claire" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]
        assembly[label="pydub\\nAudio Assembly" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]
        publish[label="GitHub Releases\\n+ RSS Feed" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]
    }}

    // Operations
    subgraph cluster_ops {{
        label="Operations" style="filled,rounded" fillcolor="#FDF2F8"
        color="{OPS_BORDER}" fontcolor="{OPS_BORDER}" fontsize="12"
        bot    [label="Telegram Bot\\nRailway"    fillcolor="{OPS_COLOR}" color="{OPS_BORDER}"]
        monitor[label="CI/CD Monitor\\nClaude Analysis" fillcolor="{OPS_COLOR}" color="{OPS_BORDER}"]
        summary[label="Daily Summary\\nStatus Reports" fillcolor="{OPS_COLOR}" color="{OPS_BORDER}"]
    }}

    // Edges: Sources -> Processing
    pubmed -> main
    preprints -> main
    journals -> main
    news -> main
    regulatory -> main
    trials -> main
    stocks -> main
    social -> main
    financial -> main

    main -> dedup
    dedup -> claude
    claude -> fallback [style="dashed" label="fail" color="#DC2626" fontcolor="#DC2626"]

    guidelines -> claude [style="dashed" color="{KNOWLEDGE_BORDER}"]
    papers -> claude [style="dashed" color="{KNOWLEDGE_BORDER}"]

    // Processing -> Delivery
    claude -> email
    claude -> beehiiv
    claude -> pages
    claude -> webpy
    fallback -> email [style="dashed"]
    webpy -> webrepo [label="GitHub API" color="{WEBSITE_BORDER}" fontcolor="{WEBSITE_BORDER}"]
    webrepo -> vercel [color="{WEBSITE_BORDER}"]

    // Weekly
    pages -> weekly_comp [style="dashed" label="daily HTML"]
    weekly_comp -> weekly_claude
    weekly_claude -> email [style="dashed"]
    weekly_claude -> pages [style="dashed"]

    // Podcast
    weekly_claude -> script [style="dashed" label="weekly content"]
    script -> tts
    tts -> assembly
    assembly -> publish

    // Ops
    bot -> main [style="dashed" label="triggers" color="{OPS_BORDER}"]
    monitor -> main [style="dashed" label="monitors" color="{OPS_BORDER}"]
    summary -> bot [style="dashed" color="{OPS_BORDER}"]
}}
"""))


# ──────────────────────────────────────────────
# 2. DAILY PIPELINE
# ──────────────────────────────────────────────
print("2. Daily Pipeline...")
render("02_daily_pipeline", textwrap.dedent(f"""\
digraph daily_pipeline {{
    graph [fontname="Helvetica" fontsize="12" bgcolor="white" pad="0.5"
           rankdir="TB" label="Daily Digest Pipeline" labelloc="t"
           labelfontsize="16" labelfontcolor="#1E293B" ranksep="0.5"]
    node [{NODE_ATTRS}]
    edge [{EDGE_ATTRS}]

    start [label="GitHub Actions\\n6 AM Central" fillcolor="#DBEAFE" color="#2563EB" shape="oval"]

    fetch [label="Fetch 9 Sources\\n(isolated error handling)" fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]

    dedup [label="Dedup Filter\\nSQLite SHA256" fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}" shape="cylinder"]

    check [label="New articles?" fillcolor="#F3F4F6" color="#6B7280" shape="diamond"]

    skip [label="Skip\\n(no digest)" fillcolor="#FEE2E2" color="#DC2626" shape="oval"]

    claude1 [label="Claude API\\nAttempt 1" fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]
    wait [label="Wait 30s" fillcolor="#F3F4F6" color="#6B7280" shape="ellipse"]
    claude2 [label="Claude API\\nAttempt 2" fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]
    fallback [label="Fallback\\nPlain HTML" fillcolor="#FEE2E2" color="#DC2626"]

    subgraph cluster_publish {{
        label="Publish (parallel)" style="filled,rounded" fillcolor="#ECFDF5"
        color="{DELIVER_BORDER}" fontcolor="{DELIVER_BORDER}"
        email   [label="Email\\nSMTP" fillcolor="{DELIVER_COLOR}" color="{DELIVER_BORDER}"]
        beehiiv [label="Beehiiv\\nAPI v2" fillcolor="{DELIVER_COLOR}" color="{DELIVER_BORDER}"]
        ghpages [label="GitHub\\nPages" fillcolor="{DELIVER_COLOR}" color="{DELIVER_BORDER}"]
        website [label="Vercel\\nWebsite" fillcolor="{WEBSITE_COLOR}" color="{WEBSITE_BORDER}"]
    }}

    mark [label="Mark Articles\\nSeen in DB" fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]
    save [label="Save for\\nWeekly" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]
    done [label="Done" fillcolor="#D1FAE5" color="#059669" shape="oval"]

    start -> fetch -> dedup -> check
    check -> skip [label="no"]
    check -> claude1 [label="yes"]
    claude1 -> email [label="success"]
    claude1 -> wait [label="fail" style="dashed" color="#DC2626"]
    wait -> claude2
    claude2 -> email [label="success"]
    claude2 -> fallback [label="fail" style="dashed" color="#DC2626"]
    fallback -> email

    email -> mark [label="success"]
    email -> done [label="fail" style="dashed" color="#DC2626" fontcolor="#DC2626"]
    claude1 -> beehiiv [label="success" style="invis"]
    claude1 -> ghpages [style="invis"]
    claude1 -> website [style="invis"]
    email -> beehiiv [style="invis"]

    mark -> save -> done
}}
"""))


# ──────────────────────────────────────────────
# 3. PODCAST PIPELINE
# ──────────────────────────────────────────────
print("3. Podcast Pipeline...")
render("03_podcast_pipeline", textwrap.dedent(f"""\
digraph podcast {{
    graph [fontname="Helvetica" fontsize="12" bgcolor="white" pad="0.5"
           rankdir="LR" label="Podcast Generation Pipeline" labelloc="t"
           labelfontsize="16" labelfontcolor="#1E293B" nodesep="0.5"]
    node [{NODE_ATTRS}]
    edge [{EDGE_ATTRS}]

    weekly [label="Weekly\\nDigest" fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]

    script [label="Claude\\nScript Writer\\n(2-host dialogue)" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]

    subgraph cluster_tts {{
        label="OpenAI TTS" style="filled,rounded" fillcolor="#F5F3FF"
        color="{PODCAST_BORDER}" fontcolor="{PODCAST_BORDER}"
        nolan [label="Nolan\\n(fable voice)" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]
        claire [label="Claire\\n(nova voice)" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]
    }}

    audio_proc [label="Audio Processing\\nEQ + Compression\\n+ Normalization" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]

    subgraph cluster_assets {{
        label="Audio Assets" style="filled,rounded" fillcolor="#FEFCE8"
        color="{KNOWLEDGE_BORDER}" fontcolor="{KNOWLEDGE_BORDER}"
        intro [label="Intro" fillcolor="{KNOWLEDGE_COLOR}" color="{KNOWLEDGE_BORDER}"]
        outro [label="Outro" fillcolor="{KNOWLEDGE_COLOR}" color="{KNOWLEDGE_BORDER}"]
        trans [label="Transitions" fillcolor="{KNOWLEDGE_COLOR}" color="{KNOWLEDGE_BORDER}"]
        bed   [label="Background" fillcolor="{KNOWLEDGE_COLOR}" color="{KNOWLEDGE_BORDER}"]
    }}

    assembly [label="pydub\\nAssembly" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]
    mp3 [label="Final MP3\\n+ ID3 Tags" fillcolor="#D1FAE5" color="#059669" shape="box3d"]

    transcribe [label="Whisper\\nTranscription" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]
    notes [label="Show Notes\\nMD + HTML" fillcolor="{PODCAST_COLOR}" color="{PODCAST_BORDER}"]

    release [label="GitHub\\nRelease" fillcolor="{DELIVER_COLOR}" color="{DELIVER_BORDER}"]
    rss [label="RSS Feed\\niTunes XML" fillcolor="{DELIVER_COLOR}" color="{DELIVER_BORDER}"]

    weekly -> script
    script -> nolan
    script -> claire
    nolan -> audio_proc
    claire -> audio_proc
    audio_proc -> assembly
    intro -> assembly
    outro -> assembly
    trans -> assembly
    bed -> assembly
    assembly -> mp3
    mp3 -> transcribe
    mp3 -> release
    transcribe -> notes
    release -> rss
}}
"""))


# ──────────────────────────────────────────────
# 4. VERCEL WEBSITE DATA FLOW
# ──────────────────────────────────────────────
print("4. Vercel Website Data Flow...")
render("04_website_dataflow", textwrap.dedent(f"""\
digraph website {{
    graph [fontname="Helvetica" fontsize="12" bgcolor="white" pad="0.5"
           rankdir="TB" label="Vercel Website Data Flow" labelloc="t"
           labelfontsize="16" labelfontcolor="#1E293B" ranksep="0.5"]
    node [{NODE_ATTRS}]
    edge [{EDGE_ATTRS}]

    main [label="main.py\\nAll source data" fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]

    build [label="website.py\\nbuild_website_data()" fillcolor="{WEBSITE_COLOR}" color="{WEBSITE_BORDER}"]

    subgraph cluster_transform {{
        label="Data Transformation" style="filled,rounded" fillcolor="#ECFEFF"
        color="{WEBSITE_BORDER}" fontcolor="{WEBSITE_BORDER}"
        classify [label="Classify Articles\\naortic / mitral / tricuspid\\nsurgical / trials / regulatory / financial" fillcolor="{WEBSITE_COLOR}" color="{WEBSITE_BORDER}"]
        og_img [label="Fetch OG Images\\n(first 20 articles)" fillcolor="{WEBSITE_COLOR}" color="{WEBSITE_BORDER}"]
        extract [label="Extract Executive\\nSummary + Key Points" fillcolor="{WEBSITE_COLOR}" color="{WEBSITE_BORDER}"]
        stock_fmt [label="Format Stock Data\\nEW MDT ABT BSX AVR.AX" fillcolor="{WEBSITE_COLOR}" color="{WEBSITE_BORDER}"]
        pod_ep [label="Load Podcast\\nEpisodes" fillcolor="{WEBSITE_COLOR}" color="{WEBSITE_BORDER}"]
    }}

    json [label="Structured JSON" fillcolor="#F3F4F6" color="#6B7280" shape="note"]

    merge [label="Sparse day?\\n< 5 articles" fillcolor="#F3F4F6" color="#6B7280" shape="diamond"]
    fill [label="Fill from\\nprevious day" fillcolor="#FEF3C7" color="#D97706"]

    subgraph cluster_push {{
        label="GitHub API Push" style="filled,rounded" fillcolor="#ECFDF5"
        color="{DELIVER_BORDER}" fontcolor="{DELIVER_BORDER}"
        latest [label="latest.json" fillcolor="{DELIVER_COLOR}" color="{DELIVER_BORDER}"]
        archive [label="digests/\\nYYYY-MM-DD.json" fillcolor="{DELIVER_COLOR}" color="{DELIVER_BORDER}"]
    }}

    vercel [label="Vercel\\nAuto-Deploy" fillcolor="#D1FAE5" color="#059669" shape="oval"]

    main -> build
    build -> classify
    build -> og_img
    build -> extract
    build -> stock_fmt
    build -> pod_ep

    classify -> json
    og_img -> json
    extract -> json
    stock_fmt -> json
    pod_ep -> json

    json -> merge
    merge -> fill [label="yes" style="dashed"]
    merge -> latest [label="no"]
    fill -> latest
    latest -> archive [style="invis"]
    json -> archive [style="invis"]
    merge -> archive [label="" style="invis"]

    latest -> vercel
    archive -> vercel [style="dashed"]
}}
"""))


# ──────────────────────────────────────────────
# 5. INFRASTRUCTURE
# ──────────────────────────────────────────────
print("5. Infrastructure...")
render("05_infrastructure", textwrap.dedent(f"""\
digraph infra {{
    graph [fontname="Helvetica" fontsize="12" bgcolor="white" pad="0.5"
           rankdir="LR" label="Infrastructure & Services" labelloc="t"
           labelfontsize="16" labelfontcolor="#1E293B" nodesep="0.4"]
    node [{NODE_ATTRS}]
    edge [{EDGE_ATTRS}]

    subgraph cluster_ci {{
        label="GitHub Actions (CI/CD)" style="filled,rounded" fillcolor="#F0F9FF"
        color="{SOURCE_BORDER}" fontcolor="{SOURCE_BORDER}"
        daily   [label="daily-digest\\nDaily 6 AM CT" fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
        weekly  [label="weekly-digest\\nSaturday" fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
        podcast [label="weekly-podcast\\nAfter weekly" fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
        monitor_wf [label="monitor\\nOn completion" fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
        summary_wf [label="daily-summary\\nMorning" fillcolor="{SOURCE_COLOR}" color="{SOURCE_BORDER}"]
    }}

    subgraph cluster_railway {{
        label="Railway" style="filled,rounded" fillcolor="#FDF2F8"
        color="{OPS_BORDER}" fontcolor="{OPS_BORDER}"
        bot [label="Telegram Bot\\nAlways-on" fillcolor="{OPS_COLOR}" color="{OPS_BORDER}"]
    }}

    subgraph cluster_services {{
        label="External Services" style="filled,rounded" fillcolor="#FFFBEB"
        color="{PROCESS_BORDER}" fontcolor="{PROCESS_BORDER}"
        anthropic [label="Anthropic\\nClaude API" fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]
        openai [label="OpenAI\\nTTS + Whisper" fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]
        smtp [label="SMTP\\nServer" fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]
        beehiiv_svc [label="Beehiiv" fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]
        telegram [label="Telegram\\nAPI" fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]
        gh_api [label="GitHub\\nAPI" fillcolor="{PROCESS_COLOR}" color="{PROCESS_BORDER}"]
    }}

    subgraph cluster_publish {{
        label="Publishing" style="filled,rounded" fillcolor="#ECFDF5"
        color="{DELIVER_BORDER}" fontcolor="{DELIVER_BORDER}"
        ghpages [label="GitHub Pages\\nthevalvewire.com" fillcolor="{DELIVER_COLOR}" color="{DELIVER_BORDER}"]
        gh_rel [label="GitHub\\nReleases" fillcolor="{DELIVER_COLOR}" color="{DELIVER_BORDER}"]
        vercel [label="Vercel\\nWebsite" fillcolor="{WEBSITE_COLOR}" color="{WEBSITE_BORDER}"]
    }}

    daily -> anthropic
    daily -> smtp
    daily -> beehiiv_svc
    daily -> ghpages
    daily -> gh_api [label="website push"]
    gh_api -> vercel

    weekly -> anthropic
    weekly -> smtp
    weekly -> ghpages
    weekly -> podcast [style="dashed" label="triggers"]

    podcast -> anthropic
    podcast -> openai
    podcast -> gh_rel

    monitor_wf -> anthropic
    monitor_wf -> telegram
    summary_wf -> telegram
    bot -> telegram
    bot -> anthropic
}}
"""))


print(f"\nAll diagrams saved to: {OUT}")
print("Files:")
for f in sorted(OUT.iterdir()):
    size = f.stat().st_size
    print(f"  {f.name} ({size // 1024}KB)")
