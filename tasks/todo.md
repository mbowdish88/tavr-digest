# AATS Week Launch Plan — The Valve Wire

> **2026-04-08 EOD update:** End-of-day handoff is at `tasks/2026-04-08-handoff.md`. Read that first if you're picking up the project after a break. It captures the four workstreams (website build, business plan, PDF extractor, agentic progression) and the priority list for tomorrow morning.



**Generated:** 2026-04-05 by `/plan-ceo-review` (gstack)
**Launch target:** Week of April 29, 2026 (AATS 2026), 24 days from generation date
**Mode:** Selective Expansion
**Status:** Site is live but unadvertised (soft launch); April 29 is the public/promotion launch
**Branch:** main

---

## Strategic frame

The Valve Wire is launching publicly during AATS 2026 week, the single best week of the year for this specific publication. AATS is the room where the named critical voices in CLAUDE.md (Bowdish, Badhwar, Mehaffey, Kaul, Miller, Chikwe) congregate in person. The publication's "balanced and circumspect, transcatheter has gotten ahead of the science" stance is the AATS room's institutional perspective.

**Positioning:** The Valve Wire is the official surgeon-perspective structural heart publication, launching at AATS.

**Two moats already in place:**
1. **Editorial moat** — explicit critical POV, named expert voices, balanced stance
2. **Knowledge moat** — 52 indexed landmark papers + ACC/AHA 2020 + ESC 2025 guidelines injected into every Claude prompt

**Launch trigger:** Combo of (a) AATS-week date (hard) + (b) N consecutive issues meeting a written quality bar (TBD: define rubric).

---

## Pre-launch musts (by April 29)

### Priority 1 — Port approved v2 HTML to Next.js (`redesign-hybrid` branch)
The redesign is already converged. Palette: terracotta `#c4553a` on navy `#0a1628`, dark mode fully designed. Approved HTML blueprint: `/Users/mbowdish/Downloads/the-valve-wire-dark-v2.html` (secondary reference: `/Users/mbowdish/Desktop/medical-publication.html`). Branch: `redesign-hybrid`. Worktree: `.claude/worktrees/agent-a291173c/`. The work is a **file-by-file Next.js port with user watching** — translation, not interpretation. **No background agents** (two prior attempts ended in reverts because agents patched existing code incrementally rather than porting cleanly).

- [ ] Block focused day with Claude Opus for the port
- [ ] Component mapping (already defined in memory): `Header.tsx`, `Masthead.tsx`, `EditionStrip.tsx`, `Headlines.tsx`, `MarketSnapshot.tsx`, `ArticleList.tsx`, `TrialsSidebar.tsx`, `WeeklyLongRead.tsx`, `SubscribeBar.tsx`, `Footer.tsx`
- [ ] **`SubscribeBar.tsx` is where Cherry-pick #1 (signup form) lives** — "Intelligence, not noise." tagline already approved. Wire to list provider during the port, not after.
- [ ] **Reserve a slot for the methodology page link** in `Footer.tsx` and as a trust signal near `Headlines.tsx` so Cherry-pick #4 has a designed home
- [ ] **AATS-week eyebrow / banner slot** in `Masthead.tsx` or `EditionStrip.tsx` — "VOL. III · MORNING EDITION" pattern can host an AATS 2026 modifier the week of Apr 29
- [ ] Test on dev server: `cd .claude/worktrees/agent-a291173c/site && npm run dev -- --port 3001`
- [ ] **Do NOT push to main or deploy to Vercel without explicit approval** (per memory)

### Priority 2 — Methodology writeup (cherry-pick #4, upgraded)
- [ ] Public-facing /methodology page documenting:
  - Structured article sidecar (regex-extracted, no AI)
  - Raw metadata passthrough as ground truth
  - `_validate_references()` hallucination check
  - Journal hierarchy (NEJM > JAMA > JACC > Lancet > EHJ > JACC:CI > ATS, JTCVS, EJCTS)
  - 52-paper knowledge base + guidelines injection
  - Editorial stance (balanced, circumspect, named critics)
- [ ] Linked from /about
- [ ] Trust signal on homepage links to it
- [ ] **Why it matters:** This is the credibility document for every pitch (JACC, AATS attendees, sponsors). Without it, "AI newsletter" = slop assumption.

### Priority 3 — Signup capture (cherry-pick #1)
- [ ] Form on website (built into redesign, not bolted on)
- [ ] Captures: name, email, **role** (full audience: CT surgeon, cardiologist, interventional cardiologist, fellow/trainee, NP/PA, hospital administrator, industry, financial analyst, regulator, patient, other), institution (optional)
- [ ] Wired to list provider (decide: Buttondown, Beehiiv reactivated, ConvertKit, Substack import, other)
- [ ] Open-rate tracking enabled
- [ ] Privacy/HIPAA disclaimer if needed (you're not collecting PHI, but a clear note helps trust)
- [ ] **Note:** The full audience is broader than I originally framed it. The Valve Wire is for the entire structural heart ecosystem (clinical + administrative + industry + financial + regulatory), not just surgeons. The surgeon's editorial VOICE is the moat; the audience is the ecosystem. Role capture should reflect that.

### Priority 4 — Quality rubric (new, derived from launch trigger)
- [ ] Write down explicitly what "issue meets the bar" means:
  - Zero fabricated numbers, journals, authors, p-values, study names
  - Executive summary holds up to a domain expert reading it cold
  - Each section has at least one critical perspective when warranted
  - Hyperlinks resolve and source material backs every claim
  - Podcast script (if generated) is one Mike would put his name on
- [ ] Define N: how many consecutive issues must hit the bar before launch comfort
- [ ] Define what happens if a pre-launch issue misses the bar (delay launch? skip the issue? human-edit?)

### Priority 5 — AATS week coverage plan
- [ ] Daily AATS coverage from April 29 through May 3 (or whatever day AATS ends)
- [ ] Pre-position: pull the AATS 2026 program in advance, identify likely high-impact sessions
- [ ] Each daily AATS-week issue should highlight surgeon-perspective takes from named voices when they present
- [ ] Consider a "Valve Wire AATS Daily" subhead/banner for that week
- [ ] Optional: a synthesized "AATS 2026 in Review" weekly digest the following Saturday

### Priority 6 — Launch outreach list
- [ ] Decide who gets the announcement on April 29
- [ ] Reuse `JACC_EMAIL.pdf` and `generate_proposal.py` as inputs (existing outreach work)
- [ ] **The full audience spans 7 groups, not just surgeons.** Outreach should reflect that breadth even though AATS week is the launch hook. Suggested categories:
  - **Clinical (AATS room):** AATS 2026 attendees / program committee (highest leverage for the launch hook)
  - **Clinical (cardiology):** Interventional cardiology program directors, structural heart program leads, ACC structural heart council members
  - **Clinical (general cardiology / fellows):** Cardiothoracic AND interventional cardiology fellowship program directors
  - **Cited critical voices** (Bowdish, Badhwar, Mehaffey, Kaul, Miller, Chikwe) — may already include you; ensure they get personal outreach
  - **Health system / administrative:** Service line directors at the top 25-50 valve programs by volume (the editor's institution, Mayo, Cleveland Clinic, Mass General, Mount Sinai, etc.)
  - **Industry:** Select contacts at Edwards, Medtronic, Abbott, Boston Scientific (relationship-building, not selling). Important: include even though you may sometimes be critical of their devices — the publication is for them too.
  - **Financial:** Sell-side analysts covering med devices at the top 5-8 firms (Morgan Stanley, Evercore ISI, Wells Fargo, Bernstein, Piper Sandler, BTIG, Jefferies, etc.)
  - **Regulatory:** Selected FDA CDRH and CMS contacts where appropriate (judgment call — relationship-dependent)
  - **Trusted colleagues** at the editor's institution and beyond who would amplify
- [ ] Draft the announcement copy (reuse generate_proposal.py output if applicable). Tone: "publication for the structural heart ecosystem, written from a surgeon's perspective." NOT "publication for surgeons."
- [ ] Decide channel: personal email vs newsletter blast vs LinkedIn post vs all three. Likely all three with different copy for each audience segment.

---

## NEW (added 2026-04-08 EOD) — Tier 2 / Tier 3 launch path items

### Business plan (Tier 2 — week 1)
- **Status:** Not started. Named tonight. The artifact that doesn't exist yet.
- **Why it matters:** the project has gotten big enough that "side project with editorial voice" is no longer a sufficient mental model. Need a written document that lays out HOW The Valve Wire becomes a real business with money flowing through it. Without it, every commercialization decision is a guess.
- **Effort:** 2-3 hours focused for v1. Co-author with Claude Opus directly (no skill needed).
- **Output:** `tasks/business-plan-v1.md`
- **The 10 sections:** Executive summary · Publication & moats · Market & audience · Revenue model · Unit economics · Go-to-market · Financial projections · Team & org · Risks & mitigations · Next 90 days
- **Open questions a business plan must answer:** Free vs paid at launch? Which audience segment is the first paid user? Sponsorship strategy? CME accreditation timing? Platform play (medweb-template) priority? Year-1 revenue target?
- **Priority:** Tomorrow morning Apr 9, second block after pen-name decision.

### Website build — Next.js port of CHOSEN-tabloid-3col-v1.html (Tier 1 — weeks 1-3)
- **Status:** Blueprint committed. Port not started.
- **Branch strategy:** New `redesign-tabloid-3col` from main. Vercel auto-deploys preview URLs.
- **Within the branch:** big-bang rewrite, file-by-file with Opus directly, no background agents, translation not interpretation.
- **Component dependency order:** globals → chrome → hero → sections → wiring → pipeline change → methodology page → other routes → signup form → /qa → /design-review → merge → /canary
- **Effort:** 14-20 hours focused, spread over 5-7 days
- **Open architectural questions:** branch name (recommend redesign-tabloid-3col), list provider (Buttondown), pipeline change in summarizer.py for tabloid_headline + tabloid_deck fields, multi-route extension order
- **Blocked by:** pen-name decision (CEO discussion), then partially by business plan v1 for SubscribeBar form fields

### PDF extractor for institution-firewalled papers (Tier 4 — post-launch)
- **Status:** Architecture sketched 2026-04-08. Not started. **DO NOT BUILD BEFORE LAUNCH.**
- **Goal:** Daily/weekly automated download of high-impact structural-heart papers from behind the institutional firewall. Drop into `knowledge/papers/inbox/` for the existing indexer to process.
- **Architecture (full sketch in `tasks/2026-04-08-handoff.md`):**
  1. Journal TOC monitor — RSS / DOI feeds for NEJM, JAMA, JACC, Lancet, EHJ, JTCVS, ATS, EJCTS
  2. Relevance scorer — Claude prompt for Valve-Wire-relevance
  3. Fetch queue — `data/fetch_queue.json` of target DOIs
  4. PDF fetcher — opens DOIs via institutional EZproxy with stored cookies (refreshed weekly via gstack `/setup-browser-cookies`)
  5. Drop to inbox — existing `knowledge/indexer.py` processes them
  6. Auto-injection into daily Claude prompts via existing `papers_index.json`
- **Files to build:** `sources/journal_toc.py`, `sources/relevance_scorer.py`, `tools/pdf_fetcher.py`, `tools/institution_auth.py`, `data/fetch_queue.json`
- **Effort:** ~1-2 days focused engineering
- **Where it runs:** NOT GitHub Actions (cookies expire and shouldn't be in CI secrets). Local cron on Mac, Eggar (Mac Mini), or Beckett (OpenClaw machine). Or triggered manually via Telegram command when at an institution-network machine.
- **CRITICAL:** Defer until after AATS launch. If something goes wrong and institutional IT flags your account, you lose institutional access right before the launch. Too much risk for the timing.

### Agentic progression — multi-agent infrastructure for tavr-digest (Tier 4 — post-launch)
- **Status:** Strategic shift named 2026-04-08. Infrastructure exists, just unused for tavr-digest.
- **The framing:** Solo + interactive Claude Code sessions doesn't scale. Need parallel work happening behind the scenes so the user stops being the bottleneck.
- **Infrastructure already in place:** GitHub Actions cron (running ✅), OpenClaw on Beckett (set up ✅), project kanban at localhost:3000 (running ✅), Telegram bot on Railway (running ✅), gstack `/schedule` and `/loop` skills (available, never used), Claude Agent SDK (available, never used)
- **Background-eligible vs interactive-only framework:**
  - Background-eligible: scheduled fetches, indexing, relevance scoring, drafting, monitoring, reporting
  - Interactive-only: strategic decisions, editorial taste, anything with the editor's name on it before review
  - The art is keeping the line clear
- **The 5 candidate background agents (priority order):**
  1. PDF fetcher behind institutional firewall (workstream above)
  2. AATS 2026 program scraper (time-sensitive, AATS is Apr 29)
  3. Paper relevance scorer (runs after PDF indexing)
  4. Outreach list enricher (find institution, role, recent pubs, contacts)
  5. Daily site canary (gstack `/canary` skill on `/loop` schedule)
- **Long-term architectural project:** Wire OpenClaw on Beckett to tavr-digest tasks. Give Beckett natural-language tasks, it spawns Claude Code sessions via ACP, does the work, commits results. User wakes up to find work done.
- **Effort:** Each agent is 1-2 days. Whole infrastructure is a multi-week project.
- **Tier 4 (post-launch):** None of this gets the publication launched on April 29.

---

## Deferred to post-launch (cherry-picks not in scope for April 29)

### Cherry-pick #2 — Podcast ROI instrumentation
- **Why deferred:** No listeners to instrument until post-launch promotion exists. The 2-week kill-decision gate is premature when there's no denominator.
- **Post-launch action:** Add download/play counts (Spotify for Podcasters, Apple Podcasts Connect, or HTTP referer logging on the GitHub Releases MP3 URLs). Run for 2 weeks post-launch. Then make the keep/kill decision with real data.

### Cherry-pick #3 — Dormant code retirement (`beehiiv.py`, `substack.py`)
- **Why deferred:** Trivial hygiene work, no launch impact. Also gated on cherry-pick #1's choice of list provider. If Beehiiv gets reactivated, only `substack.py` should go.
- **Post-launch action:** Pick list provider, then delete or archive the loser(s).

### Other candidates surfaced but not built into a cherry-pick
- **Vertical-2 dogfooding (`medweb-template`)** — Way too late for April 29. Defer until post-launch and only after vertical 1 has paying readers / proven demand. Premature platform talk dilutes focus.
- **Podcast root-cause reliability fix** — Last 30 days of commits show 8+ podcast firefights (timeouts, retries, push races). Symptoms of "Anthropic load" being treated with longer timeouts. Real fix is idempotent retry + partial-state recovery + manual resume. Post-launch.
- **Reader identity survey** — Replaced by signup-form role capture (cherry-pick #1).

---

## Strategic findings (for future reference)

### Strengths confirmed
1. Editorial moat is real and rare in AI medical content
2. Knowledge moat (52 papers + guidelines) is expensive to replicate
3. Domain focus (structural heart, not all cardiology) is correct — narrow beachhead
4. Anti-hallucination architecture is thoughtful and worth surfacing publicly (drives priority 2)
5. Pipeline runs daily and has been shipping consistently

### Gaps identified
1. **No subscriber identity** — being addressed by cherry-pick #1
2. **Podcast eats reliability budget with unknown ROI** — being addressed by cherry-pick #2 (post-launch)
3. **Platform play is phantom scope** — retired from near-term goals, deferred indefinitely
4. **Commercialization scaffolding is zero** — Stripe, paywall, sponsor slots not built. Defer until post-launch when subscriber count justifies
5. **Complexity creep without retirement** — addressed by cherry-pick #3 (post-launch)

### The risk that almost stayed hidden
**"Optimize quality before launching" can become "never launch" without an explicit trigger.** April 29 + quality rubric is the explicit trigger. If a pre-launch issue misses the bar, the rule must be defined NOW, not in the moment.

---

## Open questions (for next session)

1. What list provider for cherry-pick #1? (Buttondown / Beehiiv / ConvertKit / Substack / other)
2. What's N in "N consecutive issues must hit the bar"? (Suggest 3 or 4)
3. What's the policy if a pre-launch issue misses the bar? (Skip? Delay launch? Human edit?)
4. Who's on the launch outreach list? (Specific names, not categories)
5. Is the JACC_EMAIL.pdf pitch separate from the AATS launch, or part of it?
6. Does the redesign in progress already include any cherry-pick #1 or #4 elements, or are they net-new?

---

## Next session

The user is taking a focused day with Claude Opus to port the approved v2 HTML to Next.js components on `redesign-hybrid`. This CEO review hands off to that port session.

**Bring this document into the port session** so the launch artifacts (signup form in `SubscribeBar.tsx`, methodology page slot in `Footer.tsx` + trust signal, AATS-week eyebrow in `Masthead.tsx`/`EditionStrip.tsx`) are baked into the port instead of bolted on after.

After the port lands, return to this document and execute Priorities 2-6.

---

## Step 0 — Distinctive design exploration ✅ COMPLETE (committed 2026-04-08)

After 6 iterations across 4 days (15 HTML mockups in claude.ai + 4 hand-built mockups in Claude Code), the chosen direction is **NY Post tabloid energy in a three-column responsive grid** with the Blue Figures cover image as a publication seal in the masthead.

**Blueprint:** `docs/designs/CHOSEN-tabloid-3col-v1.html`

**Key elements:** Red NY Post masthead, Blue Figures cover seal (92px), black kicker strip with yellow stars, 3-col hero (lead = 92pt type-as-visual headline NO IMAGE / middle = 3 secondary stories / right = live monitor + listen + trials teaser), full-width black editorial callout with red borders, trials grid, red subscribe band with yellow CTA, black footer, responsive collapse at <768px.

**Typography:** Big Shoulders Display (wordmark, headlines), Fraunces variable (body, italic), Space Grotesk (nav, meta), JetBrains Mono (live monitor)

**Full decision doc:** `tasks/2026-04-05-design-decision.md`

**Open question (deferred to CEO discussion):** Pen-name vs real-name byline. The mockup hardcodes "Michael Bowdish, MD · Editor" but the live site uses a pen name. Strategic decision required before AATS launch — single CSS variable swap once decided.

---

## The Procedure — how to actually do the HTML → Next.js port

Inputs in place: approved palette (terracotta `#c4553a` on navy `#0a1628`) **— may be replaced by Step 0 output**, blueprint (`~/Downloads/the-valve-wire-dark-v2.html` **— may be replaced by `~/Downloads/the-valve-wire-distinctive-v1.html` from Step 0**), worktree at `.claude/worktrees/agent-a291173c/`, branch `redesign-hybrid` reset to clean Phase 1.

**This is a translation task, not a design task.** Every step below exists to prevent the agent from anchoring to existing code and producing another reverted Phase 2.

### Step 1 — Confirm the blueprint is still right
```bash
open ~/Downloads/the-valve-wire-dark-v2.html
```
Look at it. If anything is off, fix the HTML in a separate context-free Claude conversation FIRST. The blueprint is the source of truth. Do not "fix" it during the port — that reintroduces the anchoring problem.

### Step 2 — Switch to the worktree
```bash
cd ~/projects/tavr-digest/.claude/worktrees/agent-a291173c
git status   # confirm on redesign-hybrid, Phase 1 is HEAD
```

### Step 3 — Start the dev server in one terminal
```bash
cd site && npm run dev -- --port 3001
```
Leave it running. Refresh `http://localhost:3001` after every component port to verify visually before moving to the next.

### Step 4 — Open a fresh Claude Opus session in this directory
Opening prompt (the constraint sentences are what prevent the failure mode):

> I have an approved HTML blueprint at `~/Downloads/the-valve-wire-dark-v2.html`. I need to port it to Next.js components in this repo, file by file, with me watching every change. **This is a translation task: copy the CSS and HTML from the blueprint directly, do not interpret, do not improvise, do not reach for "best practices" that depart from the source.** I will tell you which component to port next. Start with `Header.tsx`.

### Step 5 — Port one component at a time, in this order
1. `Header.tsx` — nav + dark/light theme toggle. Small, builds confidence.
2. `Footer.tsx` — 3-column footer. Small, includes the methodology page link slot.
3. `Masthead.tsx` — two-tone wordmark ("The Valve" cream + "*Wire*" terracotta italic). Signature visual.
4. `EditionStrip.tsx` — vol/edition + inline tickers. Anchors the masthead.
5. `Headlines.tsx` — numbered "Today's Intelligence" briefing, ~720px constraint.
6. `ArticleList.tsx` + `TrialsSidebar.tsx` — two-column layout, most of the page area.
7. `MarketSnapshot.tsx` — 4-column financial grid (incl. "Global TAVR Procedures").
8. `WeeklyLongRead.tsx` — podcast play button left, editorial text right.
9. **`SubscribeBar.tsx` LAST** — the launch button. "Intelligence, not noise." tagline already approved. Wire to a list provider in the same session if you've decided which one. If not, leave the form action as a TODO with a clear comment so cherry-pick #1 lands cleanly later.

**After EVERY component port, refresh `:3001` and visually compare to the blueprint side-by-side.** If something drifted, stop and fix it before moving on. Do not let drift accumulate.

### Step 6 — When component-complete, run rendered-output gstack skills
```
/qa http://localhost:3001
/design-review http://localhost:3001
```
These are SAFE skills (they operate on rendered output, not source). They will catch what file-by-file translation missed: spacing, hover states, dark-mode toggling, mobile breakpoints, broken links, missing empty/loading/error states.

### Step 7 — Merge to main and deploy
```
/ship
/land-and-deploy
```
**Do not skip approval.** Per `feedback_deploy_approval` in memory: never deploy visual changes to the live site without explicit go-ahead. Ask before pushing. Watch with `/canary` after deploy.

---

## Three temptations that will break the procedure (don't)

1. **"Let me just spawn a background agent to do the boring components in parallel."**
   No. That's the failure mode. Background agents = local minimum = reverted Phase 2 again.

2. **"Opus knows how to write Next.js better than the v2 HTML pattern, let me let it improvise this one component."**
   No. The blueprint is the source of truth. If the blueprint is wrong, fix the blueprint in a separate context-free session. Improvisation in the port reintroduces the anchoring problem.

3. **"Let me try `/design-html` instead of doing this manually."**
   No. `/design-html` is in the "not recommended" list above precisely for this reason. The skill description is aspirational. Use Opus directly.

---

## Pre-flight checklist (do this BEFORE the focused day)

If you have one hour before the focused day starts, the highest-leverage thing is to **open the v2 HTML and confirm it's still what you want**. If it's not, you do not want to discover that mid-port.

- [ ] `open ~/Downloads/the-valve-wire-dark-v2.html` — confirm the blueprint
- [ ] `open ~/Desktop/medical-publication.html` — confirm the secondary reference
- [ ] Decide on a list provider for `SubscribeBar.tsx` (Buttondown / Beehiiv reactivated / ConvertKit / Substack / other)
- [ ] Skim this `tasks/todo.md` once so the procedure is in your head when you start
- [ ] Block the calendar for the focused day, treat as non-negotiable

---

## Recommended gstack skills for tavr-digest

Curated from the full gstack skill list. Skipped skills that don't fit (office-hours, design-consultation, design-shotgun, autoplan, devex-review, etc) because the product, design, and team shape don't match those skills' purpose.

### The meta-rule for tavr-digest (learned the hard way)

Multiple prior redesign attempts failed because **agents pattern-match to existing code** even with excellent prompts and "start from scratch" instructions. The model anchors to whatever is in the repo and produces variants of it, not departures from it. Background/parallel agents make this WORSE, not better — they each rediscover the same local minimum.

**Rule for this project:** use gstack skills that operate on **rendered output** (dev server, deployed site) or **measurement**. Do the **creative work directly with Opus**, no agents on rails inside the existing codebase. This split matters, and getting it wrong has already cost two redesign cycles.

### Top 5 for the next 24 days (AATS launch path)

1. **The Opus port itself (NOT a gstack skill)** — Sit with Claude Opus directly, file by file, port the v2 HTML to Next.js components. No background agents. No `/design-html`. The user watches every file. This is the gating work and it cannot be delegated to a skill without risking another reverted overhaul.

2. **`/qa`** — Systematic QA test of a web app, then iterative bug-fix loop with atomic commits. Run against the dev server (`cd .claude/worktrees/agent-a291173c/site && npm run dev -- --port 3001`) after each component port lands. **Safe because it operates on rendered output, not source code.** Catches broken interactions, edge cases, missing states.

3. **`/design-review`** — Designer's-eye visual audit of the rendered site. Finds spacing issues, hierarchy problems, AI slop patterns, slow interactions. **Safe because it operates on rendered output.** Run after the port is component-complete but before merging to main. Catches what file-by-file translation missed.

4. **`/canary`** — Post-deploy monitoring loop. Watches the live Vercel site for console errors, performance regressions, broken pages. **Critical after the redesign hits production** — the previous overhaul (b7bd457) was reverted within a day. Canary catches that class of failure faster.

5. **`/ship`** + **`/land-and-deploy`** — Pre-merge: tests, diff review, version bump, CHANGELOG, PR creation. Post-merge: wait for CI, deploy, verify prod via canary. **Safe because they're workflow orchestration, not creative work.** Use as the bridge from `redesign-hybrid` → `main` → Vercel.

### Pre-launch but secondary

6. **`/cso`** — OWASP + STRIDE + supply-chain security audit. Worth running ONCE before the AATS-week public push. Surface area is real: Telegram bot on Railway, GitHub Actions secrets, SMTP credentials, Anthropic + OpenAI API keys, SEC EDGAR + yfinance feeds, Beehiiv (if reactivated). Pre-launch is the right time to find what's exposed.

7. **`/investigate`** — Systematic four-phase root-cause debugging. **Recommended for the recurring podcast reliability issues.** The last 30 days of commits show 8+ podcast firefights treated by extending timeouts (300s → 900s → 6 hours). That pattern is symptom-treatment, not root cause. `/investigate` enforces the discipline of finding the actual failure mode before patching.

### Post-launch

8. **`/plan-eng-review`** — Architecture and tests review of the pipeline. Run after launch when there's headroom to think about complexity reduction (dormant code, podcast architecture, source module sprawl).

9. **`/document-release`** — Closes out a milestone by updating README/ARCHITECTURE/CHANGELOG/CLAUDE.md to match what shipped. Run after AATS-week launch to mark the milestone formally.

10. **`/health`** — Code quality dashboard with composite score and trend tracking. Useful as a baseline measurement before and after the post-launch cleanup work.

11. **`/benchmark`** — Performance regression detection. Useful as a baseline after the redesign port lands, so any future change is measured against it.

### Always-on directive (already in CLAUDE.md)

- **`/browse`** is the only allowed browser tool. Never `mcp__claude-in-chrome__*`. This directive is already in the project CLAUDE.md so any agent will see it.

### Skills explicitly NOT recommended

- **`/design-html`** — In theory works from approved mockups, but it's still an agent on rails inside the existing repo. Non-trivial risk it falls into the same pattern-matching trap as the previous reverted redesigns. **Use Opus directly instead.**
- `/office-hours`, `/design-consultation`, `/design-shotgun` — product/design exploration. Not needed; both are converged. Also: would burn tokens producing more variants of the existing-code anchor.
- `/plan-ceo-review` — already done (this session, 2026-04-05).
- `/plan-design-review` — design-stage review. Design is past that stage.
- `/plan-eng-review` — useful in principle for post-launch architecture cleanup, but its recommendations may anchor to incremental refactor patches. Use with judgment.
- `/devex-review`, `/plan-devex-review` — developer experience for external users. Solo project, no DX surface.
- `/autoplan` — chains all reviews together. Heavy machinery, and inherits the anchoring failure mode at multiple steps.
- `/freeze`, `/guard`, `/careful`, `/unfreeze` — safety guardrails. Use only situationally when touching production-sensitive paths.
- `/checkpoint`, `/learn`, `/retro` — useful tools but not load-bearing for the AATS launch path.
