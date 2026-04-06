# NEJM Enhanced — alternate direction prompt

**Use:** Paste into the same claude.ai conversation that produced the v3 tabloid set (so the model has full context). Or paste into a fresh conversation if you also paste the v2 NEJM HTML (`docs/designs/explorations/v2-1-nejm-print.html`) as starting context.

**What this is:** A refinement of the NEJM print era v2 direction (the quiet authoritative one) that adds two specific enhancements I suggested earlier — the vitals monitor strip from the OR minimalism direction, and the H&E pathology palette accents from the surgeon's dossier direction. **This is the alternative to the chosen tabloid direction.** If after sleeping on it you decide the tabloid pick is too risky, this gives you a stronger NEJM-cluster fallback that's better than NEJM v2 alone.

---

## THE PROMPT (copy from here to the end)

Take the NEJM print era v2 direction you produced — the one with the 1985 NEJM aesthetic: EB Garamond + Crimson Pro typography, ivory background (#f7f2ea), chamber-red accents, drop cap on the lead, small caps section heads, justified body text. I am keeping that direction as a serious candidate for launch, but I want to enhance it with two specific moves I'm porting in from your other directions. Produce ONE new HTML file (not five) — this is a refinement of the existing NEJM v2, not a new exploration.

The aesthetic stays NEJM print era 1985. Do NOT make this look tabloid. Do NOT add bold sans-serif headlines. Do NOT use red banner mastheads. The NEJM gravitas is the entire point of this direction. The two enhancements should feel like layers on top of a journal, not like a redesign.

### Enhancement 1: Vitals monitor strip at the very top of the page

Add a thin dark bar across the very top of the page, ABOVE the NEJM masthead. It should look like a hospital vitals monitor (Philips IntelliVue or GE anesthesia monitor aesthetic). Specifications:

- Position flush at the very top of the viewport, full width, no margin above
- Background: dark vitals-monitor green-black (#0c1a14 or similar)
- Text: light vitals-monitor green (#a0d8b8 or similar)
- Font: JetBrains Mono or similar monospace, 9-10pt, lowercase or smallcase
- Letter-spacing: 0.06-0.10em
- Padding: 8-10px vertical, 24px horizontal
- Border-bottom: 2px solid surgical green (#2a6e4a)

Content of the strip (use verbatim, two columns flexed apart):
- **Left:** `● LIVE · ISSUE 47 · APR 28 2026 · 06:00 ET`
- **Right:** `EW 98.40 ▲ · MDT 84.20 ▼ · ABT 112.80 ▲ · BSX 76.55 ▲`

The leading `●` on the left is a pulsing SpO2-style indicator. Use a CSS @keyframes animation, 2-second cycle, opacity 0.4 to 1.0, ease-in-out infinite. Color it with a brighter monitor green (#30b060) so it reads as alive.

The NEJM masthead begins immediately below this strip — no spacing between them. The reader should feel like they walked past a hospital monitor and into a journal.

This single element adds a "live, current, breathing" dimension to the otherwise serene academic page. It is the signature visual move that nobody else in medical newsletters is doing. Treat it as the most important new element.

### Enhancement 2: H&E pathology palette accents

Augment the existing NEJM color palette with two specific accent colors borrowed from histopathology stains:

- **H&E pink** `#c87080` — use this for podcast callout boxes and any podcast-related label
- **H&E purple** `#7858a0` — use this for editorial commentary callouts (see Enhancement 3) and any editorial-voice section heads

Keep the existing chamber-red, oxygenated red, venous blue, and muscle coral colors from v2 — do NOT replace them. Layer the H&E pink and purple in addition. The total palette becomes:
- Chamber red (existing) — masthead title, primary accents
- Oxygenated red (existing) — journal source tags
- Venous blue (existing) — FDA / regulatory source tags, trials
- Muscle coral (existing) — separators, ornaments
- **H&E pink (new)** — podcast block background and border
- **H&E purple (new)** — editorial callout, "EDITORIAL" label

Specific changes from v2:
- The podcast block (currently fascia cream with muscle coral border) becomes light H&E pink background `#f8e8ec` with H&E pink border `#c87080`. The "This Week's Podcast" label color becomes H&E pink.
- The "Editorial Summary" section head color changes from tissue-red to H&E purple `#7858a0`.

### Enhancement 3: Add an "editorial commentary" callout box

Add a NEW structural element after the three secondary headlines and before the endmatter (trials/industry/podcast section). This is a small callout box containing a brief editorial paragraph in the surgeon's voice. It is the visual signal that this publication has a POINT OF VIEW.

Style:
- Width: same as the article items above (max 640px center column)
- Background: light H&E purple `#f2ecf6`
- Left border: 4px solid H&E purple `#7858a0`
- Padding: 14px 18px
- Top label: "EDITORIAL" in H&E purple, small caps, 8pt, letter-spacing 0.2em, weight 700
- Body: EB Garamond italic, 10.5pt, color #1a1a1a, line-height 1.6
- Body content (use verbatim):

"The PARTNER 3 5-year readout is being celebrated as a TAVR victory. It is. But the structural valve deterioration signal in the TAVR arm at year 5 is a story the device community is going to spend the next two AATS meetings trying to explain. Read the back-half of the paper before you read the press release."

This is the editorial voice made structural. The visual stays quiet and journal-like, but this small callout signals "we have opinions and we will share them."

### Everything else stays the same

Real Valve Wire content stays the same as v2 — masthead, executive summary, three headlines, sidebar (trials, industry watch, podcast), subscribe bar, footer. Use it all verbatim. The two enhancements (vitals strip + H&E accents + editorial callout) are additions, not replacements.

Typography stays EB Garamond + Crimson Pro. Layout stays single 640px center column. Background stays ivory `#f7f2ea`. Drop cap stays on the lead. Small caps section heads stay. Justified body text stays.

### Output

Produce ONE self-contained HTML file: `nejm-enhanced-v3.html`. Real content, opens in browser cleanly. No external dependencies beyond the Google Fonts I already used in v2 plus JetBrains Mono for the vitals strip.

### What I will judge by

I am keeping this as a fallback to a tabloid direction. The decision rule is: does this NEJM-enhanced direction feel meaningfully better than NEJM v2, AND does it remain quiet enough that a financial analyst at Bernstein or an FDA reviewer would still respect it? If yes, it becomes a real alternative. If the enhancements break the NEJM gravitas, the v2 unchanged is still my fallback.

Begin.
