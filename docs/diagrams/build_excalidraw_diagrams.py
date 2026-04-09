#!/usr/bin/env python3
"""
Generate four Excalidraw flow diagrams for The Valve Wire:
  1. AATS launch flow (21-day countdown)
  2. Audience ecosystem map (7 segments)
  3. Site information architecture (post-redesign)
  4. Reader journey / subscriber funnel

Outputs four .excalidraw files into ~/projects/tavr-digest/docs/diagrams/.
"""

import json
import random
import os
from pathlib import Path

OUT_DIR = Path.home() / "projects" / "tavr-digest" / "docs" / "diagrams"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Reproducible IDs (so the files are stable across regenerations)
random.seed(42)


def rand_id() :
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=20))


def rand_seed() :
    return random.randint(1, 2**31 - 1)


# ───────────────────────────────────────────
# Element factories
# ───────────────────────────────────────────

def base_props() :
    return {
        "angle": 0,
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "index": None,
        "roundness": {"type": 3},
        "seed": rand_seed(),
        "versionNonce": rand_seed(),
        "isDeleted": False,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
    }


def box(x: int, y: int, w: int, h: int, fill: str, stroke: str = "#1e1e1e", id_=None) :
    el = base_props()
    el.update({
        "id": id_ or rand_id(),
        "type": "rectangle",
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "backgroundColor": fill,
        "strokeColor": stroke,
        "strokeWidth": 2,
    })
    return el


def diamond(x: int, y: int, w: int, h: int, fill: str, id_=None) :
    el = base_props()
    el.update({
        "id": id_ or rand_id(),
        "type": "diamond",
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "backgroundColor": fill,
        "strokeWidth": 2,
        "roundness": None,
    })
    return el


def ellipse(x: int, y: int, w: int, h: int, fill: str, stroke: str = "#1e1e1e", id_=None) :
    el = base_props()
    el.update({
        "id": id_ or rand_id(),
        "type": "ellipse",
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "backgroundColor": fill,
        "strokeColor": stroke,
        "strokeWidth": 2,
        "roundness": None,
    })
    return el


def text(x, y, content, size=16, color="#1e1e1e", align="center", width=None):
    el = base_props()
    line_count = content.count("\n") + 1
    line_height = 1.25
    h = int(size * line_height * line_count) + 4
    if width is None:
        max_line_len = max(len(line) for line in content.split("\n"))
        width = max(int(max_line_len * size * 0.55), 60)
    el.update({
        "id": rand_id(),
        "type": "text",
        "x": x,
        "y": y,
        "width": width,
        "height": h,
        "strokeColor": color,
        "fillStyle": "solid",
        "roundness": None,
        "text": content,
        "fontSize": size,
        "fontFamily": 5,  # Excalifont
        "textAlign": align,
        "verticalAlign": "top",
        "baseline": int(size * 0.85),
        "containerId": None,
        "originalText": content,
        "lineHeight": line_height,
        "autoResize": True,
    })
    return el


def boxed_text(x: int, y: int, w: int, h: int, label: str, fill: str, stroke: str = "#1e1e1e",
               size: int = 14) :
    """A rectangle plus a centered text element. Returns (rect, text)."""
    rect = box(x, y, w, h, fill, stroke)
    # Centered text inside the box
    line_count = label.count("\n") + 1
    line_height = 1.25
    text_h = int(size * line_height * line_count)
    text_y = y + (h - text_h) // 2
    txt = text(x + 8, text_y, label, size=size, align="center", width=w - 16)
    return rect, txt


def arrow(x1: int, y1: int, x2: int, y2: int, color: str = "#1e1e1e", dashed: bool = False) :
    el = base_props()
    el.update({
        "id": rand_id(),
        "type": "arrow",
        "x": x1,
        "y": y1,
        "width": abs(x2 - x1),
        "height": abs(y2 - y1),
        "strokeColor": color,
        "strokeWidth": 2,
        "strokeStyle": "dashed" if dashed else "solid",
        "roundness": {"type": 2},
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": "arrow",
        "elbowed": False,
    })
    return el


def line_(x1: int, y1: int, x2: int, y2: int, color: str = "#1e1e1e", dashed: bool = False) :
    el = base_props()
    el.update({
        "id": rand_id(),
        "type": "line",
        "x": x1,
        "y": y1,
        "width": abs(x2 - x1),
        "height": abs(y2 - y1),
        "strokeColor": color,
        "strokeWidth": 2,
        "strokeStyle": "dashed" if dashed else "solid",
        "roundness": {"type": 2},
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": None,
    })
    return el


def write_excalidraw(filename: str, elements: list, name: str):
    """Wrap elements in the Excalidraw file structure and write to disk."""
    payload = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {
            "gridSize": 20,
            "gridStep": 5,
            "gridModeEnabled": False,
            "viewBackgroundColor": "#ffffff",
        },
        "files": {},
    }
    out_path = OUT_DIR / filename
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  ✓ {name} → {out_path}")
    return out_path


# Color palette (consistent across all 4 diagrams)
RED = "#f8d7da"      # critical / launch / red brand
RED_BORDER = "#c41e3a"
BLUE = "#d4e4f0"     # data / publication / Blue Figures
BLUE_BORDER = "#1a3a5e"
GREEN = "#d1e7dd"    # delivery / success
GREEN_BORDER = "#0f5132"
AMBER = "#fff3cd"    # process / in-progress
AMBER_BORDER = "#664d03"
PURPLE = "#e2d9f3"   # editorial / decisions
PURPLE_BORDER = "#4a3475"
GRAY = "#e9ecef"     # support / context
GRAY_BORDER = "#495057"
NAVY_DARK = "#18324e"


# ═══════════════════════════════════════════════════════════
# DIAGRAM 1 — AATS LAUNCH FLOW (21-day countdown)
# ═══════════════════════════════════════════════════════════

def diagram_launch_flow():
    elements = []

    # Title
    elements.append(text(40, 30,
                         "The Valve Wire — AATS Launch Flow",
                         size=28, color=NAVY_DARK, align="left"))
    elements.append(text(40, 70,
                         "21-day countdown · Apr 8 → Apr 29 · Critical path in red",
                         size=14, color="#5a6080", align="left"))

    # Timeline base line
    elements.append(line_(60, 200, 1640, 200, color="#999"))

    # Date markers
    dates = [
        ("Apr 8\nTODAY", 60),
        ("Apr 9-10", 230),
        ("Apr 11-13", 400),
        ("Apr 14-16", 570),
        ("Apr 17-20", 740),
        ("Apr 21-23", 910),
        ("Apr 24-27", 1080),
        ("Apr 28", 1330),
        ("Apr 29\nLAUNCH", 1530),
    ]
    for label, x in dates:
        elements.append(line_(x + 60, 195, x + 60, 215, color="#999"))
        elements.append(text(x, 220, label, size=12, color="#5a6080", align="center", width=120))

    # Milestone boxes (above the line = critical path, below = parallel)
    # Critical path (red border, above the line)
    critical = [
        ("CEO discussion\nPen-name decision", 40, 100, RED, RED_BORDER),
        ("Next.js port\nfile-by-file w/ Opus", 220, 100, RED, RED_BORDER),
        ("Methodology page\ncredibility doc", 400, 100, RED, RED_BORDER),
        ("First quality issue\n(rubric defined)", 570, 100, RED, RED_BORDER),
        ("Issues 2-4\nbar must hold", 740, 100, RED, RED_BORDER),
        ("Outreach list\nfinalized", 910, 100, RED, RED_BORDER),
        ("Light verify\nsleep", 1310, 100, AMBER, AMBER_BORDER),
        ("ANNOUNCE\nAATS week", 1530, 100, NAVY_DARK, RED_BORDER),
    ]
    for label, x, y, fill, stroke in critical:
        rect, txt = boxed_text(x, y, 160, 65, label, fill, stroke=stroke, size=12)
        elements.extend([rect, txt])

    # Parallel work (below the line)
    parallel = [
        ("Signup form\nwire to provider", 220, 280, BLUE, BLUE_BORDER),
        ("Quality rubric\nwritten down", 400, 280, AMBER, AMBER_BORDER),
        ("AATS coverage plan\npre-position program", 740, 280, PURPLE, PURPLE_BORDER),
        ("Daily AATS coverage\nMay 3", 1080, 280, GREEN, GREEN_BORDER),
    ]
    for label, x, y, fill, stroke in parallel:
        rect, txt = boxed_text(x, y, 160, 65, label, fill, stroke=stroke, size=12)
        elements.extend([rect, txt])

    # Critical path arrows
    critical_pts = [120, 300, 480, 650, 820, 990, 1390, 1610]
    for i in range(len(critical_pts) - 1):
        elements.append(arrow(critical_pts[i] + 65, 165, critical_pts[i+1] - 5, 165,
                              color=RED_BORDER))

    # Legend
    elements.append(text(40, 400, "LEGEND", size=14, color=NAVY_DARK, align="left"))
    legend_items = [
        ("Critical path (must complete in order)", RED, RED_BORDER, 430),
        ("Parallel work (can run alongside)", BLUE, BLUE_BORDER, 460),
        ("Editorial / quality control", AMBER, AMBER_BORDER, 490),
        ("Coverage / outreach", PURPLE, PURPLE_BORDER, 520),
        ("Launch milestone", NAVY_DARK, RED_BORDER, 550),
    ]
    for label, fill, stroke, y in legend_items:
        elements.append(box(40, y, 18, 18, fill, stroke=stroke))
        elements.append(text(70, y + 1, label, size=13, color="#1e1e1e", align="left"))

    # Open question callout
    rect, txt = boxed_text(40, 620, 700, 80,
                           "OPEN QUESTION  ·  Pen name vs real name byline\nDeferred to CEO discussion. Single CSS variable swap once decided.\nBlocks the Next.js port because byline appears in masthead, callout, footer, outreach.",
                           "#fff3cd", stroke="#664d03", size=12)
    elements.extend([rect, txt])

    return elements


# ═══════════════════════════════════════════════════════════
# DIAGRAM 2 — AUDIENCE ECOSYSTEM MAP (7 segments)
# ═══════════════════════════════════════════════════════════

def diagram_audience_ecosystem():
    elements = []

    # Title
    elements.append(text(40, 30,
                         "The Valve Wire — Audience Ecosystem",
                         size=28, color=NAVY_DARK, align="left"))
    elements.append(text(40, 70,
                         "Seven segments. Surgeon's editorial voice is the moat. The audience is the entire ecosystem.",
                         size=14, color="#5a6080", align="left"))

    # Center: The publication
    cx, cy = 800, 480
    rect = box(cx - 130, cy - 60, 260, 120, NAVY_DARK, stroke=RED_BORDER)
    elements.append(rect)
    elements.append(text(cx - 110, cy - 45,
                         "THE VALVE WIRE",
                         size=22, color="#ffffff", align="center", width=220))
    elements.append(text(cx - 110, cy - 12,
                         "A surgeon's reading\nof structural heart disease",
                         size=12, color="#f0e8d0", align="center", width=220))

    # Seven segments around the center
    # Position them in a circle
    segments = [
        ("CT SURGEONS", "AATS room\nNamed critics live here\nEditorial moat audience",
         RED, RED_BORDER, 800, 130),
        ("CARDIOLOGISTS", "Non-interventional\nGeneral cardiology\nBalanced perspective",
         BLUE, BLUE_BORDER, 1280, 230),
        ("INTERVENTIONAL\nCARDIOLOGISTS", "TAVR/TMVR operators\nSometimes targets\nbut still readers",
         AMBER, AMBER_BORDER, 1450, 480),
        ("INDUSTRY EXECS", "Edwards · Medtronic\nAbbott · Boston Sci\nDevice business unit leads",
         PURPLE, PURPLE_BORDER, 1280, 730),
        ("FINANCIAL\nANALYSTS", "Sell-side · buy-side\nBernstein · MS · Wells\nAlternative to PR",
         GREEN, GREEN_BORDER, 800, 830),
        ("REGULATORS", "FDA CDRH · CMS\nCoverage decisions\nExpert third-party voice",
         GRAY, GRAY_BORDER, 320, 730),
        ("HOSPITAL\nADMINISTRATORS", "Valve clinic directors\nService line leaders\nC-suite at top programs",
         "#f8d7da", "#9a3a45", 150, 480),
    ]

    for title_, body, fill, stroke, x, y in segments:
        rect = box(x - 110, y - 55, 220, 110, fill, stroke=stroke)
        elements.append(rect)
        elements.append(text(x - 90, y - 40, title_,
                             size=14, color=stroke, align="center", width=180))
        elements.append(text(x - 90, y - 5, body,
                             size=10, color="#1e1e1e", align="center", width=180))

    # Arrows from center to each segment (and back)
    segment_centers = [(800, 130), (1280, 230), (1450, 480), (1280, 730),
                       (800, 830), (320, 730), (150, 480)]
    for sx, sy in segment_centers:
        # Compute offset to land on box edge
        dx, dy = sx - cx, sy - cy
        dist = (dx**2 + dy**2) ** 0.5
        if dist == 0:
            continue
        ux, uy = dx / dist, dy / dist
        # Center box edge offset (260x120 → max half = 130, but we approximate to 90)
        start_x = cx + ux * 90
        start_y = cy + uy * 60
        end_x = sx - ux * 100
        end_y = sy - uy * 50
        elements.append(arrow(int(start_x), int(start_y), int(end_x), int(end_y),
                              color="#888"))

    # Footer note
    elements.append(text(40, 980,
                         "Editorial moat = surgeon's voice. Distribution moat = the entire ecosystem reading it.\nDo not optimize the publication for surgeons only. The voice is the differentiator; the audience is the market.",
                         size=12, color="#5a6080", align="left"))

    return elements


# ═══════════════════════════════════════════════════════════
# DIAGRAM 3 — SITE INFORMATION ARCHITECTURE (post-redesign)
# ═══════════════════════════════════════════════════════════

def diagram_site_architecture():
    elements = []

    # Title
    elements.append(text(40, 30,
                         "The Valve Wire — Site Information Architecture",
                         size=28, color=NAVY_DARK, align="left"))
    elements.append(text(40, 70,
                         "Post-redesign · CHOSEN-tabloid-3col-v1.html → Next.js components → routes → data sources",
                         size=14, color="#5a6080", align="left"))

    # Layer 1: Routes (top)
    elements.append(text(40, 120, "ROUTES", size=14, color=NAVY_DARK, align="left"))
    routes = [
        ("/", 60, 150),
        ("/aortic", 200, 150),
        ("/mitral", 320, 150),
        ("/tricuspid", 440, 150),
        ("/archive", 580, 150),
        ("/weekly", 720, 150),
        ("/podcast", 840, 150),
        ("/about", 970, 150),
        ("/methodology", 1090, 150),
        ("/editorial", 1240, 150),
    ]
    for label, x, y in routes:
        rect, txt = boxed_text(x, y, 110, 50, label, BLUE, stroke=BLUE_BORDER, size=14)
        elements.extend([rect, txt])

    # Layer 2: Components (middle)
    elements.append(text(40, 240, "COMPONENTS", size=14, color=NAVY_DARK, align="left"))
    components_row1 = [
        ("Masthead\nred banner + seal", 60, 270),
        ("KickerBar\nblack + yellow stars", 240, 270),
        ("SectionNav\ncategory links", 420, 270),
    ]
    components_row2 = [
        ("HeroLead\n92pt headline\ntype-as-visual", 60, 380),
        ("HeroMiddle\n3 secondary stories", 260, 380),
        ("HeroRight\nLive monitor +\nListen + Trials", 460, 380),
        ("EditorialCallout\nblack band\nred borders", 660, 380),
    ]
    components_row3 = [
        ("TrialsSection\n3-card grid", 60, 510),
        ("SubscribeBar\nred + yellow CTA", 240, 510),
        ("Footer\nblack · 5 columns", 420, 510),
    ]
    for label, x, y in components_row1:
        rect, txt = boxed_text(x, y, 160, 70, label, AMBER, stroke=AMBER_BORDER, size=12)
        elements.extend([rect, txt])
    for label, x, y in components_row2:
        rect, txt = boxed_text(x, y, 180, 90, label, AMBER, stroke=AMBER_BORDER, size=11)
        elements.extend([rect, txt])
    for label, x, y in components_row3:
        rect, txt = boxed_text(x, y, 160, 70, label, AMBER, stroke=AMBER_BORDER, size=12)
        elements.extend([rect, txt])

    # Layer 3: Data sources (bottom)
    elements.append(text(40, 640, "DATA SOURCES", size=14, color=NAVY_DARK, align="left"))
    data_sources = [
        ("latest.json\nhomepage data", 60, 670),
        ("digests/\nYYYY-MM-DD.json\ndaily archive", 240, 670),
        ("podcast_episodes.json\nlisten card data", 440, 670),
        ("weekly_latest.html\nweekly route", 660, 670),
        ("Stock prices\nyfinance live", 860, 670),
        ("Trial NCT data\nClinicalTrials.gov", 1040, 670),
    ]
    for label, x, y in data_sources:
        rect, txt = boxed_text(x, y, 170, 80, label, GREEN, stroke=GREEN_BORDER, size=11)
        elements.extend([rect, txt])

    # Arrows from data sources up to components (data flow)
    elements.append(arrow(140, 670, 140, 470, color=GREEN_BORDER))
    elements.append(arrow(320, 670, 350, 470, color=GREEN_BORDER))
    elements.append(arrow(520, 670, 350, 470, color=GREEN_BORDER))
    elements.append(arrow(740, 670, 140, 580, color=GREEN_BORDER, dashed=True))
    elements.append(arrow(940, 670, 550, 470, color=GREEN_BORDER))
    elements.append(arrow(1120, 670, 140, 580, color=GREEN_BORDER, dashed=True))

    # Pipeline source (off to the right)
    rect, txt = boxed_text(1230, 670, 200, 80,
                           "Daily Pipeline\nmain.py → Claude Opus\n→ writes data files",
                           PURPLE, stroke=PURPLE_BORDER, size=11)
    elements.extend([rect, txt])
    elements.append(arrow(1230, 710, 1100, 710, color=PURPLE_BORDER))

    # Footer note
    elements.append(text(40, 800,
                         "Data flow: pipeline writes JSON files → Vercel auto-deploys on push → components read at request time.\nAll content pages use dynamic = \"force-dynamic\" so the latest data is served on every request.",
                         size=12, color="#5a6080", align="left"))

    # Open architectural questions
    elements.append(text(40, 870, "OPEN ARCHITECTURAL QUESTIONS", size=14, color=RED_BORDER, align="left"))
    questions = [
        "1. Branch strategy: redesign-tabloid-3col cut from main",
        "2. List provider for SubscribeBar: Buttondown (recommended)",
        "3. summarizer.py needs new tabloid_headline + tabloid_deck fields",
        "4. Multi-route extension: 30 min whiteboard before any code",
    ]
    for i, q in enumerate(questions):
        elements.append(text(60, 900 + i * 24, q, size=12, color="#1e1e1e", align="left"))

    return elements


# ═══════════════════════════════════════════════════════════
# DIAGRAM 4 — READER JOURNEY / SUBSCRIBER FUNNEL
# ═══════════════════════════════════════════════════════════

def diagram_reader_funnel():
    elements = []

    # Title
    elements.append(text(40, 30,
                         "The Valve Wire — Reader Journey & Subscriber Funnel",
                         size=28, color=NAVY_DARK, align="left"))
    elements.append(text(40, 70,
                         "Discovery → first visit → signup → engaged reader → paid subscriber (eventually)",
                         size=14, color="#5a6080", align="left"))

    # Top layer: Discovery channels (wide)
    elements.append(text(40, 130, "DISCOVERY CHANNELS", size=14, color=NAVY_DARK, align="left"))
    channels = [
        ("AATS booth\n+ in-person", 60, 160),
        ("Colleague link\n(WoM)", 240, 160),
        ("LinkedIn\n+ X / BlueSky", 420, 160),
        ("Methodology\npage SEO", 600, 160),
        ("Podcast\n(Apple/Spotify)", 780, 160),
        ("Press / journal\nmention", 960, 160),
        ("Industry\nintroductions", 1140, 160),
    ]
    for label, x, y in channels:
        rect, txt = boxed_text(x, y, 160, 70, label, BLUE, stroke=BLUE_BORDER, size=12)
        elements.extend([rect, txt])

    # Funnel: First Visit
    rect, txt = boxed_text(280, 290, 1000, 70,
                           "FIRST VISIT  ·  ~80% bounce expected (industry baseline)",
                           "#fff3cd", stroke="#664d03", size=14)
    elements.extend([rect, txt])

    # Arrows from channels into First Visit
    for _, x, _ in channels:
        elements.append(arrow(x + 80, 230, 780, 290, color="#888"))

    # Funnel: Signup form
    rect, txt = boxed_text(380, 410, 800, 70,
                           "SIGNUP FORM  ·  Captures name, email, role, institution",
                           AMBER, stroke=AMBER_BORDER, size=14)
    elements.extend([rect, txt])
    elements.append(arrow(780, 360, 780, 410, color="#888"))

    # First issue email
    rect, txt = boxed_text(450, 530, 660, 70,
                           "FIRST ISSUE EMAIL  ·  Welcome + lead story",
                           AMBER, stroke=AMBER_BORDER, size=14)
    elements.extend([rect, txt])
    elements.append(arrow(780, 480, 780, 530, color="#888"))

    # Engaged reader
    rect, txt = boxed_text(530, 650, 500, 70,
                           "ENGAGED READER  ·  3+ issues opened, returns to site",
                           GREEN, stroke=GREEN_BORDER, size=14)
    elements.extend([rect, txt])
    elements.append(arrow(780, 600, 780, 650, color="#888"))

    # Paid subscriber (bottom)
    rect, txt = boxed_text(620, 770, 320, 80,
                           "PAID SUBSCRIBER\n(post-launch, eventually)",
                           NAVY_DARK, stroke=RED_BORDER, size=14)
    elements.extend([rect, txt])
    # White text on dark
    for el in elements[-1:]:
        el["strokeColor"] = "#f0e8d0"
    elements.append(arrow(780, 720, 780, 770, color="#888", dashed=True))

    # Side notes (right column)
    elements.append(text(1340, 290, "WHAT EACH STAGE NEEDS", size=14, color=NAVY_DARK, align="left"))
    notes = [
        ("First Visit",
         "· Loud distinctive design (✓ tabloid)\n· Methodology page (TODO)\n· Real Valve Wire content"),
        ("Signup Form",
         "· List provider wired (Buttondown)\n· Role capture (all 7 audiences)\n· No friction"),
        ("First Issue",
         "· Quality rubric defined\n· Editorial voice consistent\n· Real bylines (pen name TBD)"),
        ("Engaged Reader",
         "· Daily issue cadence\n· Open-rate tracking\n· Section navigation"),
        ("Paid Subscriber",
         "· Stripe / paywall (post-launch)\n· Value tier (intel? archive? podcast?)\n· Pricing decision (TBD)"),
    ]
    y = 320
    for stage, body in notes:
        elements.append(text(1340, y, stage, size=13, color=NAVY_DARK, align="left"))
        elements.append(text(1340, y + 22, body, size=11, color="#1e1e1e", align="left"))
        y += 95

    # Footer: launch context
    rect, txt = boxed_text(40, 880, 1500, 80,
                           "AATS LAUNCH (Apr 29) is the moment when channels 1-7 turn on at the same time. Funnel must be working before that day.\nThe channels that matter most for AATS week: in-person AATS booth, colleague WoM, LinkedIn announcement, podcast.",
                           RED, stroke=RED_BORDER, size=12)
    elements.extend([rect, txt])

    return elements


# ═══════════════════════════════════════════════════════════
# Build all four
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Building 4 Excalidraw diagrams for The Valve Wire...")
    print()
    write_excalidraw("01_aats_launch_flow.excalidraw", diagram_launch_flow(),
                     "AATS launch flow (21-day countdown)")
    write_excalidraw("02_audience_ecosystem.excalidraw", diagram_audience_ecosystem(),
                     "Audience ecosystem map (7 segments)")
    write_excalidraw("03_site_architecture.excalidraw", diagram_site_architecture(),
                     "Site information architecture (post-redesign)")
    write_excalidraw("04_reader_funnel.excalidraw", diagram_reader_funnel(),
                     "Reader journey / subscriber funnel")
    print()
    print(f"Done. 4 files written to {OUT_DIR}/")
    print()
    print("Open in Excalidraw:")
    print("  https://excalidraw.com → Open → pick the .excalidraw file")
