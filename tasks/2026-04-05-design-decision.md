# Design Decision — The Valve Wire (✅ CHOSEN: NY Post tabloid in 3 columns)

**Status:** ✅ COMMITTED 2026-04-08
**Blueprint:** `docs/designs/CHOSEN-tabloid-3col-v1.html`
**Launch target:** Week of AATS, April 29, 2026 (21 days from decision as of commit)

## What we landed on (after 6 iterations across 4 days)

**NY Post tabloid energy in a three-column responsive grid**, with the Blue Figures cover image as a small publication seal in the masthead.

- **Red NY Post masthead** (#d41920) — two-tone wordmark: white "THE VALVE" + yellow "— W I R E —"
- **Blue Figures cover as a 92px square seal** beside the wordmark — brand identity present, not dominant
- **Black kicker strip** with yellow text and ★ stars (matches original v1 tabloid)
- **3-col hero grid:**
  - LEFT (50%): Lead story with **NO image** — type-as-visual at 92pt Big Shoulders Display. The headline IS the visual. "TAVR WINS / ON MORTALITY. / **LOSES ON DURABILITY.**" with the third line in red.
  - MIDDLE (30%): Three secondary tabloid stories with bold condensed headlines, red FDA flag
  - RIGHT (20%): Live SpO2 monitor + Listen card + Trials teaser
- **Editorial callout** as a full-width black band with red borders, italic Fraunces, "FROM THE EDITOR"
- **Trials in Progress** with three navy-topped cards
- **Red subscribe band** with yellow CTA
- **Black footer** with red section labels
- **Responsive `@media` queries** collapse to single column at <768px

**Typography:** Big Shoulders Display (wordmark, headlines), Fraunces variable (body, italic), Space Grotesk (nav, meta), JetBrains Mono (live monitor)

**Why it works:** Voice and visual finally pull in the same direction. Tabloid energy matches the opinionated editorial voice. The cover image is brand identity, not a hero. Type-as-visual at 92pt is the radical move — no other medical newsletter does it. Multi-route problem solved by the 3-col grid (scales to archive, weekly, sections). Doesn't look AI-generated because it's loud, opinionated, and uses real brand assets.

## Open question (deferred to CEO discussion)

**Pen name vs real-name byline.** User flagged 2026-04-08 that the live valvewire.com uses a pen name, not "E. Nolan Beckett, MD." The mockup hardcodes "E. Nolan Beckett, MD · Editor" as a placeholder. Single CSS variable / template substitution swap if the decision goes the other way. This is a load-bearing strategic question for the editorial moat — the named-critic editorial stance loses force when the editor isn't named — and should be resolved before AATS launch.

## Rejected directions (preserved for comparison)

- `CANDIDATE-economist-modern-v1.html` — too similar to live site genre
- `CANDIDATE-bluefigures-v1.html` — still too "tasteful publication"
- `CANDIDATE-nejm-enhanced-v3.html` — academic frame dampens editorial voice + NEJM trade dress concerns
- `CANDIDATE-tabloid-v1.html` — original NY Post single-column tabloid; the 3-col version supersedes it but stays as a reference

## Next moves

1. ✅ Commit this decision and the chosen blueprint
2. Resolve the pen-name question (CEO discussion)
3. Run `/checkpoint` to capture current state for session continuity
4. Start the Next.js port on a fresh `redesign-tabloid-3col` branch from main, file-by-file with Opus directly
5. List provider for SubscribeBar.tsx (recommend Buttondown)
6. Pipeline change in `processing/summarizer.py` to produce `tabloid_headline` and `tabloid_deck` fields
7. Multi-route extension whiteboarding (~30 min before any code)
8. Methodology page, signup form, quality rubric, AATS coverage plan, launch outreach list (per `tasks/todo.md`)

---

## (HISTORICAL — superseded) The two finalists from 2026-04-06

The following section was the working state on 2026-04-06 morning when there were two finalists. Preserved for context. Both candidates were ultimately rejected in favor of the NY Post 3-col direction built on 2026-04-08.

---

## The two finalists

| | **Candidate A: Tabloid (NY Post)** | **Candidate B: NEJM Enhanced** |
|---|---|---|
| **File** | `docs/designs/CANDIDATE-tabloid-v1.html` | `docs/designs/CANDIDATE-nejm-enhanced-v3.html` |
| **Aesthetic** | NY Post front page applied to medical content | NEJM print era 1985 + vitals monitor strip + H&E pathology accents + editorial callout |
| **Headline style** | 52pt Oswald, "TAVR WINS ON MORTALITY. LOSES ON DURABILITY." with key words in red | Crimson Pro masthead, drop-cap lead, justified body, the editorial in a bordered callout box |
| **Voice/visual fit** | Voice and visual both loud — pull together | Voice has its own bordered callout — quiet journal frame around opinionated voice |
| **Multi-audience filter** | Splits — splits the room. Some surgeons love it; some analysts/regulators may think "tabloid = unserious" | Wins clean — all 7 audience segments served |
| **Distinctive concept** | Loud typography + opinionated headlines as the hero | Pulsing SpO2 vitals strip at top + editorial callout — both unique to this publication |
| **Stop-and-look factor** | Very high (visual scream) | High but quieter (the live pulsing dot is the hook) |
| **Status signal** | "We have opinions and we're loud about them" | "We are a journal, and we have opinions" |
| **Ages well** | Tabloid energy can date | Academic typography is timeless |
| **Risk to credibility** | Real | Low |
| **Operationalizes daily** | Wants a hero headline every day | Handles any number of stories naturally |

### How to pick in the morning (the 3-step procedure)

1. **Open both files in browser tabs side by side:**
   ```bash
   open ~/projects/tavr-digest/docs/designs/CANDIDATE-tabloid-v1.html
   open ~/projects/tavr-digest/docs/designs/CANDIDATE-nejm-enhanced-v3.html
   ```

2. **Apply the three-reader test.** Imagine sending the URL to:
   - (a) A CT surgeon you respect
   - (b) A sell-side analyst at Bernstein covering med devices
   - (c) The head of structural heart at a large valve program

   Would all three of them read it without hesitation? Both designs need to pass this test. If one of them clearly fails for any of the three readers, eliminate it.

3. **Trust your gut, not your taste.** Don't pick the one that looks "best." Pick the one that **feels like Mike [critic]'s publication**. Which one would you put your name on without hesitation? Which one would you screenshot and send to a colleague at AATS?

   If your gut says the same answer both times, that's the answer. Commit and move to the port.

   If your gut splits, pick the one that scared you slightly — there's information in the discomfort.

### After the decision

Whichever you pick:
1. Rename the chosen file from `CANDIDATE-` to `CHOSEN-`
2. Update this doc's title and "What we chose and why" section to reflect the pick
3. Update `tasks/todo.md` Step 0 reference
4. Update memory `project_tavr_digest.md` design decision section
5. Run the kickoff prompt at the bottom of this file (substituting the right blueprint filename) to start the Next.js port

Whichever loses goes into `docs/designs/runner-up/` for posterity.

---

## What we chose and why

After 3 iterations of distinctive-design exploration in claude.ai (15 HTML mockups across 5 visual directions × 3 iterations), the chosen direction is **literal NY Post front page tabloid energy**, applied to The Valve Wire content.

The chosen file is `docs/designs/CHOSEN-tabloid-v1.html`. It uses:
- **Red banner masthead** with two-tone "THE VALVE / WIRE" logo (Archivo Black + spaced Oswald yellow)
- **Black kicker bar** with yellow text and ★ ornament for the lead story tease
- **Massive 52pt Oswald headline** with red emphasis on key phrases
- **Roboto Condensed deck text** under the headline
- **Secondary headlines** with red/blue source badges (NEJM = red, FDA = blue)
- **Black ticker strip** for stock data
- **Yellow subscribe bar** with red CTA
- **Lora italic** for the independence note in the footer

### Why this direction (the editorial argument)

The Valve Wire's editorial voice is opinionated, urgent, and willing to call BS on hyped device technology. For weeks, attempts to design a website kept producing variants of the modern newsletter cluster (Stratechery / Substack / Axios / FT Alphaville) — quiet, restrained, "tasteful." That visual was at war with the editorial voice. The publication says "the back-half of that paper is more sobering than the press release." That is **tabloid voice, not academic voice.**

The NY Post tabloid direction makes the visual finally do the same work the words are doing. The headline "TAVR WINS ON MORTALITY. LOSES ON DURABILITY." (with the two key words in red, in 52-point Oswald) is exactly what a surgeon-perspective publication should look like. **The visual is the editorial stance made loud.**

This is also the most distinctive direction from a positioning standpoint. Every medical newsletter in existence reaches for either Stratechery-modern or NEJM-academic. The space between is empty. A tabloid-energy structural heart publication is arresting on contact because nobody is doing it. **People will screenshot it. People will share it. AATS attendees will pull out their phones and show it to other surgeons.** That's a launch advantage no other direction can provide.

### What we considered and rejected

- **NEJM print era v2** (`docs/designs/explorations/v2-1-nejm-print.html`) — A serious contender. Quiet authority, broadest multi-audience appeal, ages well. Rejected because it's a defensive play that puts visual identity in service of "trust us, we're rigorous" — which every other serious medical publication is also doing. The Valve Wire's differentiation is the opinionated voice, and the NEJM visual would dampen rather than amplify that voice. **Kept as a fallback if the tabloid direction doesn't land.**

- **Surgeon's dossier v2** (`docs/designs/explorations/v2-2-surgeon-dossier.html`) — Beautiful and distinctive but too surgeon-coded. Would alienate the non-clinical 40% of the audience (industry execs, financial analysts, regulators, hospital admins).

- **Anatomical first v2** (`docs/designs/explorations/v2-3-anatomical-first.html`) — The most chromatically rich design and the most beautiful Netter-style anatomy. Rejected because the architecture is a quarterly journal, not a daily digest, and the anatomy-as-hero structure doesn't operationalize for daily content production.

- **OR minimalism v2** (`docs/designs/explorations/v2-4-or-minimalism.html`) — Cold and clinical. The vitals-monitor strip at the top is a brilliant standalone idea (worth porting INTO whichever final design wins).

- **Retro academic v2** (`docs/designs/explorations/v2-5-retro-academic.html`) — Too retro and sterile. User feedback: "they could use more color, lol."

- **Drudge medical v3** (`docs/designs/explorations/v3-2-drudge-medical.html`) — Faithful Drudge homage, ugly on purpose. Rejected because the audience would not give it the patience Drudge requires.

- **Bloomberg Businessweek cover v3** (`docs/designs/explorations/v3-3-bbw-cover.html`) — The biggest typographic statement of any direction (82pt Anton headlines). Rejected because the magazine-cover architecture wants ONE story per page, not a daily multi-story digest.

- **NY Post sports back page v3** (`docs/designs/explorations/v3-4-backpage.html`) — Even louder than the chosen direction, with a hero data-viz zone. Rejected because the chart-as-hero format requires every issue to have a hero chart, which is hard to operationalize day to day.

- **WSJ A-Hed meets Drudge v3** (`docs/designs/explorations/v3-5-wsj-drudge.html`) — Most "shippable" of the v3 batch. Punchy headlines + Lora serif body. Rejected as Plan A but **kept as the strongest alternative** if the full tabloid direction is too risky on second look tomorrow.

### Steal-from list (port these moves into the tabloid base)

Two specific elements from the rejected directions are worth porting INTO the tabloid base because they add value without compromising the loud aesthetic:

1. **The vitals-monitor strip from OR minimalism v2** (`docs/designs/explorations/v2-4-or-minimalism.html`, see `.status-bar` and `.status-indicator` CSS). A thin dark bar across the very top of the page, JetBrains Mono font, dark vitals-monitor background, pulsing green SpO2 indicator with a 2-second animation. Sits ABOVE the red NY Post banner like a hospital monitor running above the masthead. Adds a "live, current, breathing" dimension.

2. **The H&E pathology palette from surgeon's dossier v2** (`docs/designs/explorations/v2-2-surgeon-dossier.html`, see `--he-pink` and `--he-purple` CSS variables). Use H&E pink (#c87080) for podcast callouts and H&E purple (#7858a0) for editorial commentary boxes. Adds a medical-pathology accent vocabulary without leaving the tabloid cluster.

Both are optional polish, not blocking for launch.

---

## Component map (what tomorrow's port will produce)

The blueprint is 437 lines of HTML+CSS. The Next.js port produces these components:

| File | What it is | Wires to existing data? |
|---|---|---|
| `app/(tabloid)/layout.tsx` | Page wrapper, font loading via `next/font` (Oswald, Archivo Black, Roboto Condensed, Lora), global CSS vars | New |
| `app/(tabloid)/globals.css` | The CSS variables (`--post-red`, `--newsprint`, `--yellow-accent`, etc), reset, base typography | New |
| `Masthead.tsx` | Red banner, two-tone "THE VALVE / WIRE" logo, vol/issue/editor on right | Hardcoded for now, eventually from config |
| `KickerBar.tsx` | Black bar, yellow text, ★ kicker line | From `latest.json` (kicker derived from lead headline) |
| `Hero.tsx` | Big 52pt Oswald headline + deck | From `latest.json` executive summary — needs a transformation |
| `SecondaryHeadlines.tsx` | The 2 secondary stories with red/blue source badges | From `latest.json` top stories — needs source-color mapping |
| `DataStrip.tsx` | Black ticker bar with stock prices | From `latest.json` stocks data (already exists) |
| `BottomGrid.tsx` | 2-col Trials + Listen | Trials from existing trials data, Listen from `podcast_episodes.json` |
| `SubscribeBar.tsx` | Yellow bar + red CTA + email form | NEW — needs list provider wired (TBD) |
| `Footer.tsx` | 3-col footer, methodology link, independence note | Static + methodology page link (also not built yet) |
| `app/(tabloid)/page.tsx` | The homepage that assembles all of these | Reads `latest.json` |

**Order of porting (in order of dependency and confidence):**
1. `globals.css` + `layout.tsx` (foundation, no logic, just typography and color setup)
2. `Masthead.tsx` (signature visual, builds confidence, no data)
3. `Footer.tsx` (small, no data)
4. `KickerBar.tsx` (small, hardcoded for first pass)
5. `Hero.tsx` (the big one — establish the typographic anchor)
6. `SecondaryHeadlines.tsx`
7. `DataStrip.tsx`
8. `BottomGrid.tsx`
9. `SubscribeBar.tsx` LAST (wires to list provider — needs decision)
10. `page.tsx` (assembly)

Refresh `:3001` after every component port and visually compare to `docs/designs/CHOSEN-tabloid-v1.html` opened in another browser tab.

---

## Open questions (need answers before or during tomorrow's port)

1. **Branch strategy.** Three options:
   - (a) Continue on `redesign-hybrid` branch (replacing the existing steel-blue/crimson redesign work)
   - (b) New branch `redesign-tabloid` from main (clean diff, recommended)
   - (c) Inside the worktree at `.claude/worktrees/agent-a291173c/`

   **Recommended: option (b).** Clean diff, no conflict with prior redesign attempts, easy to revert if needed.

2. **List provider for `SubscribeBar.tsx`.** Options:
   - **Buttondown** (recommended): single API key, 5-minute setup, free tier covers stealth phase
   - **Beehiiv** (reactivate dormant code): requires figuring out what dormant `delivery/beehiiv.py` is still functional
   - **ConvertKit**: most full-featured SaaS, takes longest to set up
   - **Substack**: form would have to be hosted externally; loses in-page form

   **Default if no decision: Buttondown.**

3. **Data transformation for `Hero.tsx`.** The existing pipeline writes `site/public/data/latest.json` with the daily digest in a structured format. The tabloid layout needs a 6-12 word HEADLINE plus a deck, not the existing exec-summary structure. Three paths:
   - (a) **Pipeline change** (right answer): modify the Claude prompt in `processing/summarizer.py` to produce a `tabloid_headline` and `tabloid_deck` field alongside the existing exec summary. The pipeline runs daily so tomorrow's issue would have the new fields.
   - (b) **Render-time derivation** (lossy): the page derives a headline from the existing exec summary at render time. Loses editorial control.
   - (c) **Hardcode for now**: ship with sample content, fix in week 2.

   **Recommended: (a), but only after the homepage is visually working.** Get the layout right first, then change the pipeline once the data shape is locked.

4. **Other routes** (`/archive`, `/weekly`, `/podcast`, `/about`). The tabloid blueprint only addresses `/`. Three options:
   - (a) Port all routes to tabloid for AATS week (most consistent, most work)
   - (b) Port only `/` and `/about` for AATS week, leave others on the old design (jarring)
   - (c) Build a "classic / tabloid" toggle that lets readers switch (most ambitious, also a signature feature)

   **Recommended: (a) if time allows, (b) if time gets tight.** Defer (c) to post-launch.

5. **Methodology page** (`Priority 2` from launch plan). Cherry-pick #4. Not started. Should land before AATS week. Tomorrow we should at minimum scaffold the route and a placeholder so the footer link in the new design is not broken.

---

## Tomorrow morning kickoff (paste AFTER you've picked between A and B)

**Step 1 — Open both finalists and pick one** (see "How to pick in the morning" above). Rename the winning file from `CANDIDATE-` to `CHOSEN-` so the kickoff prompt below has a definite reference.

**Step 2 — Open Claude Code in `~/projects/tavr-digest`.** Make sure you're on Claude Opus 4.6. Paste this prompt (substitute the actual chosen blueprint filename):

> I'm picking up the Valve Wire redesign port from yesterday's CEO review session. The full context is in `tasks/2026-04-05-design-decision.md`. Read that file first.
>
> Decision committed this morning: we're porting `docs/designs/CHOSEN-{tabloid-v1 OR nejm-enhanced-v3}.html` into Next.js components on a new branch `redesign-{tabloid OR nejm}` cut from main. This is a translation task, not a design task: copy the HTML and CSS from the blueprint directly, do not interpret, do not improvise, do not reach for "best practices" that depart from the source. I am watching every file you produce.
>
> Start with Step 1 of the porting procedure: create the branch, then create `app/(redesign)/globals.css` with all the CSS variables and base typography from the blueprint. Show me the file before moving to component 2. Do not skip ahead. No background agents.
>
> Before starting, ask me for a decision on the list provider for `SubscribeBar.tsx` (Buttondown vs Beehiiv vs ConvertKit vs Substack — Buttondown is recommended) so I have the answer ready by the time we get to that component.

That's the entire kickoff. Everything else is in this file or in `tasks/todo.md`.

---

## Status summary

- **Blueprint locked:** `docs/designs/CHOSEN-tabloid-v1.html`
- **All 15 explorations preserved:** `docs/designs/explorations/v[1-3]-[1-5]-*.html`
- **Component map:** Above (10 files in dependency order)
- **Open questions:** 5 (recommended defaults given for each)
- **Time estimate:** 2-4 hours focused for the homepage; 1-2 days for full launch-ready
- **Next session:** Tomorrow morning, fresh Claude Code session, kickoff prompt above
