# AATS Week Launch Plan — The Valve Wire

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
- [ ] Captures: name, email, role (cardiologist / surgeon / fellow / NP / industry / patient / other), institution (optional)
- [ ] Wired to list provider (decide: Buttondown, Beehiiv reactivated, ConvertKit, Substack import, other)
- [ ] Open-rate tracking enabled
- [ ] Privacy/HIPAA disclaimer if needed (you're not collecting PHI, but a clear note helps trust)

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
- [ ] Suggested categories:
  - AATS 2026 attendees / program committee (highest leverage)
  - Cited critical voices (Bowdish, Badhwar, Mehaffey, Kaul, Miller, Chikwe) — may already include you
  - Cardiothoracic fellowship program directors
  - Trusted colleagues at Cedars-Sinai and beyond who would amplify
  - Valve industry contacts (relationship-building, not selling)
- [ ] Draft the announcement copy (reuse generate_proposal.py output if applicable)
- [ ] Decide channel: personal email vs newsletter blast vs LinkedIn post vs all three

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
