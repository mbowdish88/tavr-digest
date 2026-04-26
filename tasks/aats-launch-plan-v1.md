---
title: "The Valve Wire — AATS 2026 Launch Plan"
subtitle: "For review · Consolidated from tasks/todo.md + 2026-04-08-handoff.md"
author: "E. Nolan Beckett, MD"
date: "2026-04-11"
geometry: margin=1in
fontsize: 11pt
mainfont: "Georgia"
colorlinks: true
linkcolor: "[RGB]{163,32,35}"
urlcolor: "[RGB]{163,32,35}"
---

# Executive Summary

**The Valve Wire** launches publicly during **AATS 2026 week (April 29 – May 3, 2026)** — **18 days out**. The publication has been running a live daily pipeline since March and is technically autonomous on the editorial side, but four things must land before the launch is a real launch: a **website redesign port**, a **written business plan**, a **pen-name decision**, and a **quality rubric**. None of these are optional. Everything else in this document — the 5 cherry-picks, the outreach list, the AATS-week coverage plan — depends on those four being resolved first.

The strategic bet is that AATS week is the single best week of the year for this publication, because the named critical voices (Badhwar, Mehaffey, Kaul, Miller, Chikwe) congregate in person and the publication's balanced, circumspect editorial stance *is* the AATS room's institutional perspective. Launching any other week leaves that leverage on the table.

---

# Where We Are (2026-04-11)

**Green:**

- Daily pipeline shipping clean issues to the editor's inbox and `data/weekly/` on a 6 AM CT GitHub Actions cron. Last 6 days all published (04-05 → 04-10).
- Website live at **thevalvewire.com** on Vercel (Next.js, monorepo at `site/`). Unadvertised. Serves as soft-launch floor.
- 52 indexed landmark papers + ACC/AHA 2020 + ESC 2025 guidelines injected into every Claude prompt. Knowledge moat is real.
- Weekly podcast pipeline runs Saturday morning via `workflow_run` off `weekly-digest`. Published to GitHub Releases + RSS.
- Monitoring: `monitor.py` + always-on Telegram bot (`@valve_wire_monitor_bot`) on Railway. Alerts on failures.
- Design decision **committed**: NY Post tabloid 3-col (`docs/designs/CHOSEN-tabloid-3col-v1.html`). Six iterations. Settled.
- Four Excalidraw diagrams committed (`docs/diagrams/0[1-4]_*.excalidraw`): AATS launch flow, audience ecosystem, site IA, reader journey.
- GitHub Actions workflows bumped to Node 24. Daily pipeline clean post-bump.

**Yellow:**

- Weekly-podcast workflow had a `git pull --rebase` bug that failed tonight's run. Fixed (commit `899e8c2`), new music swapped in (`1c26f29`, `6b1e978`), re-triggered. End-to-end validation pending — if it fails again we need to debug before calling the pipeline launch-ready.
- Website redesign port **not started**. 14–20 hours of focused translation work remaining.
- No `data/weekly/2026-04-11.html` yet because today's daily pipeline hasn't run. Expected by 06:15 CT.

**Red (decision-blocked, not work-blocked):**

- **Pen-name byline unresolved.** Blocks masthead, editorial callout, footer, outreach copy. The CHOSEN blueprint hardcodes "E. Nolan Beckett, MD · Editor" as a placeholder.
- **Business plan does not exist.** Blocks SubscribeBar form fields, monetization framing, outreach positioning, year-1 target.
- **Quality rubric does not exist.** The launch trigger is "AATS date + N consecutive issues meeting a written quality bar" — the bar is not written.

---

# Timeline to AATS

**Today:** 2026-04-11 (Saturday) · **Launch:** 2026-04-29 (Wednesday) · **T-minus 18 days**

| Window | Dates | Primary work |
|---|---|---|
| **Decisions week** | Apr 11 – Apr 13 (Sat–Mon) | Pen-name decision. Business plan v1. List provider pick. |
| **Port week 1** | Apr 14 – Apr 20 | Next.js port: chrome → hero → sections → wiring. Dev on Vercel preview URL from `redesign-tabloid-3col` branch. Methodology page. |
| **Port week 2** | Apr 21 – Apr 27 | Remaining routes (`/aortic`, `/mitral`, `/tricuspid`, `/archive`, `/weekly`, `/podcast`, `/about`, `/editorial`). `/qa` and `/design-review` against preview. Merge to main. `/canary`. Pre-launch security pass (`/cso`). |
| **Launch week** | Apr 28 – May 3 | **Apr 29 (Wed):** public launch + AATS daily coverage begins. **Apr 29 – May 3:** daily AATS coverage. **May 4 (Sat):** "AATS 2026 in Review" weekly + podcast. |
| **Post-launch** | May 4+ | Reader instrumentation, podcast ROI data, business plan v2, post-launch retro. |

**Slack:** 18 days for 14–20 hours of port work is technically comfortable (2 hours/day avg), but the port can't start until the pen-name decision lands, and once started it must run clean — this project has already had two reverted redesign attempts. Plan as if the real working window is 12 days, not 18.

---

# The Four Workstreams

## 1. Website Build (Tier 1 · weeks 1–3 · **blocking**)

**What:** Port the committed NY Post tabloid 3-col blueprint (`docs/designs/CHOSEN-tabloid-3col-v1.html`) to Next.js components in the `site/` directory of the monorepo.

**Branch strategy:** new `redesign-tabloid-3col` from main. Vercel auto-deploys preview URLs for branches → live site stays on old design while port runs at a preview URL.

**Within the branch:** big-bang rewrite, NOT incremental swap. The two designs are too structurally different to mix.

**Method:** file-by-file port with **Opus directly — translation, not interpretation**. Copy CSS verbatim from the blueprint. **No background agents.** This is the hard-won lesson from two prior reverts: agents pattern-match to existing code on creative tasks and produce variants of the repo instead of departures from it.

**Component dependency order (~14–20 hours total):**

1. Branch + globals (CSS vars, fonts via `next/font`, base typography) · ~1 h
2. Chrome: `Masthead.tsx`, `KickerBar.tsx`, `SectionNav.tsx`, `Footer.tsx` · ~1 h
3. Hero: `HeroLead.tsx` (92pt headline), `HeroMiddle.tsx` (3 secondary), `HeroRight.tsx` (monitor + listen + trials) · ~2 h
4. Sections: `EditorialCallout.tsx`, `TrialsSection.tsx`, `SubscribeBar.tsx` · ~1 h
5. Wire to data: `latest.json`, `podcast_episodes.json`, ticker · ~1 h
6. Pipeline change in `processing/summarizer.py` for `tabloid_headline` + `tabloid_deck` fields · ~1–2 h
7. Methodology page (public credibility doc) · ~1 h
8. Other routes (`/aortic`, `/mitral`, `/tricuspid`, `/archive`, `/weekly`, `/podcast`, `/about`, `/editorial`) · ~3–4 h
9. Signup form wiring to list provider · ~1 h
10. `/qa` against preview URL · ~1 h
11. `/design-review` against preview URL · ~1 h
12. Merge to main + Vercel production + `/canary` · ~30 min + ongoing

**Blocked by:** pen-name decision (before step 2) · business plan v1 (before step 4, for SubscribeBar fields).

**Do not deploy to production without explicit approval.** Per memory: two prior overhauls were reverted within a day.

## 2. Business Plan (Tier 2 · week 1 · **partially blocking**)

**Why:** the project has grown past "side project with editorial voice." Without a written document laying out *how* The Valve Wire becomes a real business with money flowing through it, every commercialization decision is a guess — and several of those decisions (free vs paid at launch, which audience is the first paid user, what the SubscribeBar collects for) affect the port.

**Effort:** 2–3 hours focused for v1, co-authored section-by-section with Claude Opus.

**Output:** `tasks/business-plan-v1.md`.

**10 sections:**

1. Executive summary
2. Publication & moats (editorial, knowledge, design)
3. Market & audience (TAM by segment, priority order, willingness-to-pay)
4. Revenue model (subs vs sponsorships vs data licensing vs CME)
5. Unit economics (cost/issue, gross margin, CAC/LTV)
6. Go-to-market & launch plan (AATS week + first 90 days)
7. Financial projections (Y1, Y2, Y3)
8. Team & org (when does an editorial assistant make sense?)
9. Risks & mitigations (pen-name credibility, AI reliability, institutional access, competitive entry, launch failure recovery)
10. Next 90 days (ordered execution)

**Critical decisions this doc must answer:**

- Free vs paid at launch? Freemium with what tiers?
- First-paid-user target segment?
- Sponsorship strategy? At what scale?
- CME accreditation — in scope for year 1?
- Platform play (`medweb-template`) — deferred, or active?
- Year-1 revenue / runway target?

## 3. PDF Extractor for Institutional Firewall (Tier 4 · **post-launch**)

**Status:** Architecture sketched 2026-04-08. Not started. **Do not build before launch.**

**Why deferred:** the workflow involves cookie-based authentication through institutional EZproxy. If anything triggers institutional IT to flag the account, you lose institutional access right before launch. The blast radius is too large for the timing. Post-launch only.

**Architecture (sketch for reference):**

```
Journal TOC monitor (NEJM/JAMA/JACC/Lancet/EHJ/JTCVS/ATS/EJCTS)
    → Relevance scorer (Claude prompt)
    → Fetch queue (data/fetch_queue.json)
    → PDF fetcher (EZproxy + stored cookies via /setup-browser-cookies)
    → knowledge/papers/inbox/
    → Existing indexer.py processes + injects into papers_index.json
```

**Files to build (when we get there):** `sources/journal_toc.py` · `sources/relevance_scorer.py` · `tools/pdf_fetcher.py` · `tools/institution_auth.py` · `data/fetch_queue.json` (~1–2 days engineering).

## 4. Agentic Progression (Tier 4 · **post-launch** · with one pre-launch carve-out)

**The framing:** solo interactive Claude Code sessions don't scale. Parallel work needs to happen in the background so the editor stops being the bottleneck.

**Pre-launch carve-out — podcast reliability sprint (3–4 hours total, fills in between other work):** making the existing weekly-podcast workflow genuinely hands-off is NOT building a new agent, it's making existing autonomy actually work. That matters pre-launch. Minimum scope:

1. Pre-flight `git status --porcelain` check at start of publish step (~20 min)
2. Dry-run the git finishing dance in CI against a fake remote (~1 h)
3. Telegram failure ping with last 30 lines of failed step (~30 min)
4. `git add -A` against a whitelist path pattern instead of three hardcoded paths (~30 min)
5. One deliberate failure drill 3 days before launch (~30 min)

**Everything else stays Tier 4 / post-launch:** the 5 candidate background agents (PDF fetcher, AATS program scraper, relevance scorer, outreach enricher, site canary), OpenClaw wiring, multi-agent dispatcher. All great. None get the publication launched on April 29.

---

# Priority Order (the actual work queue)

**Week 1 (Apr 11 – Apr 13) — Decisions + Foundation**

1. **Pen-name decision** (30–45 min). CEO-level. Decide and commit to one. Blocks everything downstream.
2. **Business plan v1** (2–3 h). Co-author with Opus. Output: `tasks/business-plan-v1.md`.
3. **List provider decision** (5 min, inside business plan session). Recommend: **Buttondown** (5-min setup, free tier covers stealth).
4. **Quality rubric v1** (1 h). Write down what "issue meets the bar" means concretely. Define N (suggest 3 consecutive issues). Define policy if pre-launch issue misses bar (skip / delay / human edit).

**Week 2 (Apr 14 – Apr 20) — Port weeks 1**

5. Branch + globals + chrome layer · ~2 h
6. Hero components · ~2 h
7. Section components · ~1 h
8. Wire to data · ~1 h
9. Methodology page · ~1 h
10. Pipeline change in `summarizer.py` for tabloid fields · ~1–2 h

Filler between sessions: podcast reliability items #1 and #3 (pre-flight + Telegram failure ping).

**Week 3 (Apr 21 – Apr 27) — Port finish + pre-launch**

11. Remaining routes · ~3–4 h
12. Signup form wired to Buttondown · ~1 h
13. `/qa http://preview-url` · ~1 h
14. `/design-review http://preview-url` · ~1 h
15. `/cso` security pass · ~2 h
16. Launch outreach list finalized (specific names) · ~2 h
17. AATS 2026 program review — identify likely high-impact sessions · ~1 h
18. Announcement copy drafted per audience segment · ~2 h
19. Merge to main + Vercel production + `/canary` running · ~1 h
20. Podcast reliability items #2 and #4 (CI git dry-run + whitelist add)
21. **Apr 26–27:** podcast reliability item #5 — deliberate failure drill

**Launch week (Apr 28 – May 4)**

22. Apr 28: launch rehearsal. Send test email to yourself. Confirm site, signup, podcast RSS, Telegram alerts all working.
23. Apr 29: **public launch.** Announcement copy goes out across channels (email, LinkedIn, personal notes to key names). First AATS daily digest ships. `/canary` watching.
24. Apr 29 – May 3: daily AATS coverage, daily `/canary`, respond to signup feedback.
25. May 4: "AATS 2026 in Review" weekly + podcast. Post-launch retro starts.

---

# Open Decisions (in priority order)

| # | Decision | Blocks | Deadline |
|---|---|---|---|
| 1 | **Pen name vs real name** for byline | Website port, outreach copy | Apr 13 |
| 2 | **Free vs paid at launch** (freemium tiers?) | SubscribeBar fields, outreach positioning | Apr 13 |
| 3 | **First-paid-user target segment** | Outreach prioritization, revenue model | Apr 13 |
| 4 | **List provider** (Buttondown / Beehiiv / ConvertKit / Substack) | SubscribeBar wiring | Apr 13 |
| 5 | **N consecutive quality-bar issues** before launch | Launch trigger | Apr 13 |
| 6 | **Policy if pre-launch issue misses bar** | Launch trigger | Apr 13 |
| 7 | **Sponsorship in launch scope?** | Business plan, outreach | Apr 20 |
| 8 | **CME accreditation** — in scope for Y1? | Business plan | Apr 20 |
| 9 | **AATS daily coverage format** (separate banner? same template?) | Week 3 editorial prep | Apr 24 |
| 10 | **Launch outreach list — specific names** | Launch-week execution | Apr 26 |

---

# Outreach List Framework

The full audience spans **7 segments**, not just surgeons. The surgeon's editorial voice is the moat; the audience is the ecosystem.

| Segment | Priority | Approach |
|---|---|---|
| **AATS 2026 attendees / program committee** | 1 (highest leverage for launch hook) | Personal email to named contacts. AATS-week-specific framing. |
| **Cited critical voices** (Badhwar, Mehaffey, Kaul, Miller, Chikwe) | 2 | Personal email. They are named in the editorial frame — they must see the publication before anyone else. |
| **Interventional cardiology** (structural heart program leads, ACC council members) | 3 | Segmented email announcing the cross-specialty scope. |
| **Health system admins** (service line directors at top 25–50 valve programs) | 4 | Segmented email with business/volume framing. |
| **Industry** (Edwards, Medtronic, Abbott, Boston Scientific contacts) | 5 | Relationship email. Publication is for them too, even when critical. |
| **Financial analysts** (sell-side med devices, top 5–8 firms) | 6 | Professional email emphasizing independent perspective. |
| **Regulatory / other** (FDA CDRH, CMS contacts, fellowship program directors, patient advocacy) | 7 | Judgment-based outreach. |

**Tone across all:** "publication for the structural heart ecosystem, written from a surgeon's perspective." Not "publication for surgeons."

**Channels:** personal email (highest priority segments) + newsletter blast (broader) + LinkedIn post (public). Different copy per audience.

**Reuse assets:** `JACC_EMAIL.pdf` and `generate_proposal.py` outputs if applicable.

---

# What's Deferred (do not do before launch)

- **PDF extractor** (institutional firewall) — cookie workflow too fragile pre-launch; lose institutional access at the wrong moment and the whole thing stalls.
- **Multi-agent infrastructure / OpenClaw wiring** — infrastructure project, not launch work.
- **Cherry-pick #2 (podcast ROI instrumentation)** — no listeners yet to instrument.
- **Cherry-pick #3 (dormant code retirement: beehiiv.py, substack.py)** — trivial hygiene, no launch impact; gated on list-provider decision.
- **Vertical-2 dogfooding (`medweb-template`)** — premature platform talk dilutes focus.
- **Reader identity survey** — replaced by signup-form role capture.
- **`/office-hours`, `/plan-eng-review`, `/plan-design-review`, `/autoplan`** — either done, wrong stage, or known to trigger the pattern-matching failure mode in this codebase.
- **`/design-html` skill** — known to trigger the same failure mode as background agents on this codebase. Use Opus directly.

---

# Definition of "Launch-Ready" (Acceptance Criteria)

The launch on **April 29** is real when all of the following are true:

- [ ] Pen-name decision made and applied to the masthead/footer/outreach
- [ ] Business plan v1 committed at `tasks/business-plan-v1.md`
- [ ] Quality rubric v1 committed with explicit N and miss-the-bar policy
- [ ] Website port merged to main, deployed to thevalvewire.com, `/canary` clean for 72 h
- [ ] Methodology page live and linked from `/about`
- [ ] SubscribeBar form wired to list provider, captures role, open-rate tracking on
- [ ] Weekly podcast workflow ran successfully hands-off at least once with the new music and the git-rebase fix
- [ ] Podcast reliability items #1–4 shipped; failure drill #5 passed
- [ ] `/cso` security pass complete, critical/high findings resolved
- [ ] AATS 2026 program reviewed; high-impact sessions identified for daily coverage
- [ ] Launch outreach list has specific names (not just segments)
- [ ] Announcement copy drafted for each audience segment
- [ ] Launch rehearsal complete (test email, site check, signup check, RSS check, Telegram alerts)
- [ ] Last 3 daily digests have all passed the quality rubric (or the defined number, N)

---

# The Three Things to Protect

**1. The design decision is real and committed.** NY Post tabloid 3-col. Six iterations got there. Don't second-guess it. Don't run another design variant skill "just to check." The decision is made.

**2. The pen-name decision blocks everything downstream.** Resolve it on day 1 of decisions week. Don't let it become another iteration cycle.

**3. The business plan is the most important non-technical work this week.** Without it, every commercialization decision in the next 30 days is a guess. Co-author with Opus; do not try to write it solo from scratch.

---

*Consolidated 2026-04-11 from `tasks/todo.md` (2026-04-05 CEO review) and `tasks/2026-04-08-handoff.md` (2026-04-08 EOD handoff). Supersedes the stale `redesign-hybrid` / terracotta-palette references in `tasks/todo.md`. Living document — revise as decisions land.*
