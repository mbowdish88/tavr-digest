# Distinctive Design Exploration — paste this into a fresh claude.ai conversation

**Use:** Open claude.ai in a browser, start a NEW conversation (no project, no context). Paste the prompt below verbatim. Use Claude Opus 4.6. The output should be 5 self-contained HTML files you can open in the browser side by side.

**Why this prompt works:** It overrides Claude's training distribution average (Stratechery/Substack/Axios newsletter design) by giving explicit non-newsletter visual references that the model has to honor. Real Valve Wire content prevents lorem ipsum from masking design problems. The "do NOT" list specifically forbids the local minimum the model would otherwise reach for.

---

## THE PROMPT (copy from here to the end)

I'm building a publication called The Valve Wire. It is a daily and weekly digest of structural heart disease news (TAVR/TAVI, MitraClip, TMVR, TriClip, TTVR, surgical and transcatheter approaches) written by a cardiothoracic surgeon. The editorial stance is critical and skeptical: many transcatheter device technologies have gotten ahead of the science and clinical guidelines, and the publication is willing to say so. Named critical voices include Bowdish, Badhwar, Mehaffey, Kaul, Miller, Chikwe.

I am launching this publication at AATS 2026 (American Association for Thoracic Surgery), the week of April 29. The audience is cardiothoracic surgeons, cardiologists, fellows, and structural heart program directors. They are skeptical, expert, time-poor, and they read primary literature. They will reject anything that looks like generic AI-generated medical content.

I have tried multiple times to design a website for this publication and every attempt produces variants of the same modern newsletter aesthetic (Stratechery, Substack, Axios, Bloomberg, Lenny's): Playfair Display headlines, dark navy or burgundy headers, two-column layouts with sticky sidebars, numbered briefing items, "Intelligence, not noise" style taglines, terracotta or forest green accents on muted backgrounds. I do not want any of that. I want something that looks like it came out of a cardiothoracic surgery culture, not a tech-bro newsletter culture.

**Your task:** produce 5 self-contained HTML files, one per visual direction below. Each HTML file must:
- Be a single self-contained file with inline CSS, no external dependencies, opens in a browser cleanly
- Use the real content I provide below (not lorem ipsum, not placeholder)
- Honor the visual references I give for that direction with rigor — do NOT default to modern newsletter conventions
- Be different ENOUGH from the other 4 that they are not variants of each other

I will judge these by opening all 5 in browser tabs and comparing them side by side. If any two of them look like cousins, you have failed. They should look like they came from completely different aesthetic universes.

### The 5 directions

**Direction 1: NEJM/JAMA print era (1985).**
Visual references: a printed New England Journal of Medicine from 1985, JAMA print issues from the same period, the Annals of Thoracic Surgery in print, a Lancet print issue. Ivory or off-white background, traditional academic serif typography (Sabon, Adobe Caslon Pro, Minion Pro, NOT Playfair Display which is decorative). Generous margins. Black ink only or black + one accent color used sparingly. Section headers in small caps. No nav chrome at all — the publication should read like a printed journal that has been carefully digitized, not like a website with a top nav bar. The reader should think "this looks authoritative because it looks like real medicine."

**Direction 2: Surgeon's working dossier.**
Visual references: a cardiothoracic surgeon's case notes for grand rounds, an operating room debrief document, the kind of dense structured working file a surgeon would actually keep. Should feel personal and expert, not editorial. Marginalia. Hand-annotated feel allowed. Maybe a typewriter or monospace font for some elements. Inline EKG strip or echo waveform images as visual section dividers (you can use ASCII art or unicode block characters or simple SVG line drawings to suggest these — be creative). The conceit: "you are reading what's in Mike Bowdish's professional notebook." Intimate, dense, expert.

**Direction 3: Anatomical illustration first.**
Visual references: Frank Netter's anatomical plates of the heart, Henry Gray's anatomy, modern cardiothoracic surgery atlases. Each section of structural heart (aortic, mitral, tricuspid) should be anchored by an anatomical illustration that you create using SVG line art (suggest the illustrations with simple anatomical line drawings — aortic valve cross-section, mitral valve apparatus, tricuspid annulus). The articles are in service of the anatomy, not the other way around. The illustrations are the visual hierarchy, not the typography. Color palette: warm anatomical (rose/burgundy for tissue, cream for paper, charcoal for ink).

**Direction 4: Operating theater minimalism.**
Visual references: medical equipment UI (Philips IntelliVue, GE Healthcare anesthesia monitors), operating room lighting, surgical instrument trays. Sharp white background, surgical green accent (#3a5f4a or similar muted clinical green), high contrast clinical sans-serif typography (Helvetica Now, Söhne, Inter Tight, Berkeley Mono for data), almost no decoration, no rounded corners, no shadows, no gradients. Should look cold, precise, expensive. The conceit: "you are reading something that came out of an OR, not a coffee shop."

**Direction 5: Retro academic medical newsletter (1990s teaching hospital).**
Visual references: a printed teaching hospital newsletter from 1992, a department chair's monthly bulletin, the kind of internal publication that circulated at academic medical centers before email. Manila paper background, fixed-width typography or a workaday serif (Computer Modern, Courier, or similar), ASCII section dividers, no nav chrome, no contemporary visual conventions. Plays the "we are not trying to look modern, we are trying to look authoritative" card hard. The conceit: "this publication has been running for 30 years and your department chair reads it."

### Real Valve Wire content to use in every mockup

**Masthead text:**
- Publication name: The Valve Wire
- Tagline / sub-title: A surgeon's reading of structural heart disease
- Volume / issue: VOL. III · ISSUE 47 · APRIL 28, 2026
- Editor: Michael Bowdish, MD

**Lead executive summary (use verbatim):**
> The PARTNER 3 5-year extended follow-up published in NEJM this week shows a sustained mortality advantage for TAVR over SAVR in low-risk patients, but the structural valve deterioration signal in the TAVR arm at year 5 is the finding that the device community is not talking about. Dr. Vinod Thourani's editorial calls for caution on extending the TAVR low-risk indication to patients under 65 until we see year 10 data. Edwards stock closed up 2.1% on the headline; the back-half of the paper is more sobering than the press release.

**Three headline items (use verbatim):**

1. **NEJM** — PARTNER 3 5-year results: TAVR mortality advantage holds, but structural valve deterioration at year 5 raises questions for sub-65 indication.

2. **EACTS** — European cardiothoracic surgeons publish position paper: "Transcatheter mitral repair outcomes do not yet meet the threshold for routine use in surgical-eligible patients." Authors include Mehaffey and Chikwe.

3. **FDA 8-K (Edwards Lifesciences)** — Class I recall on a small lot of SAPIEN 3 Ultra valves due to a balloon catheter manufacturing defect. No patient harm reported. Affects approximately 3,400 units shipped Jan-Mar 2026.

**Sidebar content (use verbatim):**
- **Clinical trials in progress:** EARLY TAVR (NCT03042104), PROGRESS (NCT04889872), TRISCEND II (NCT04482062)
- **Industry watch:** Edwards Lifesciences (EW) $98.40 +2.1% · Medtronic (MDT) $84.20 −0.3% · Abbott (ABT) $112.80 +0.4% · Boston Scientific (BSX) $76.55 +0.9%
- **This week's podcast:** "PARTNER 3 at year 5: what the editorial does not say" — 18 minutes — with case discussion

**Subscribe / footer text:**
- Subscribe tagline: A surgeon's reading. Delivered daily.
- Footer columns: SECTIONS (Aortic, Mitral, Tricuspid, Surgical vs Transcatheter, Industry, Trials) · ABOUT (Editorial stance, Methodology, Editor) · ARCHIVE (By date, By topic, By journal)
- Bottom note: The Valve Wire is independent and accepts no industry funding.

### Output format

Produce 5 separate HTML files, one per direction. Label them clearly:
- `direction-1-nejm-print.html`
- `direction-2-surgeon-dossier.html`
- `direction-3-anatomical-first.html`
- `direction-4-or-minimalism.html`
- `direction-5-retro-academic.html`

Each file should contain ALL the content above (executive summary, 3 headlines, sidebar, subscribe, footer). Each file must be visually distinct from the other 4 — they should not be remixes of each other.

### What I will reject

- Anything with Playfair Display, Inter Tight, Söhne, Aktiv Grotesk, or any other contemporary newsletter typography
- Anything with a dark navy header or burgundy accent
- Anything with a two-column layout where the left column is wide content and the right column is a sticky sidebar
- Anything that looks like Stratechery, Substack, Axios, Bloomberg, Lenny's, The Information, Sherwood, Semafor, or any other contemporary news publication
- "Numbered briefing" formatting where headlines are 01, 02, 03 in a column
- Anything where the dominant visual element is the typography rather than the content structure or imagery
- Lorem ipsum or placeholder content of any kind

If you find yourself reaching for any of those, you are reverting to the training distribution average. Stop, re-read the visual references for the direction you are working on, and do something different.

Begin with Direction 1.
