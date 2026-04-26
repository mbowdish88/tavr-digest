# Podcast Pipeline Re-Engineering Roadmap

**Drafted:** 2026-04-25 (post-WSJ-rerender debug session)
**Constraint:** AATS launch 2026-04-29 (T-4 days). Don't break production before then.
**North star:** A podcast that doesn't sound like a robot reading a Claude script, with editorial gates that prevent missing front-page coverage of the field.

---

## What's wrong with the current pipeline (ranked)

| # | Problem | Evidence | Severity |
|---|---|---|---|
| 1 | TTS-1-HD is the floor on perceived quality | Voice "off and on" complaint persists even with clean assembler chain; OpenAI TTS has known cadence/breath artifacts | **Critical** |
| 2 | pydub assembly is amateur audio engineering | Was clipping silently for 4+ weeks (Apr 4 = +1.16 dB peak); no LUFS/true-peak/limiting; stacked compressors at default tunings | **Critical** |
| 3 | Script generation is single-pass on Opus | $1.40/episode locked into one Claude completion; no critique pass, no per-section iteration; lead-story decisions are roll-of-dice | **High** |
| 4 | Weekly + Scriptwriter prompts duplicate editorial logic | Today we had to add Mainstream-Press Hierarchy to BOTH. They can disagree. | **High** |
| 5 | No editorial gate before publication | Pipeline auto-runs Saturday and ships; missed the WSJ piece for that reason | **High** (user already proposing fix) |
| 6 | Source pipeline blind to paywall content | Caught WSJ only because user was a source. Bloomberg, FT, NYT all behind paywalls | **High** |
| 7 | Two-host fiction adds complexity for marginal payoff | 78 segments × stitched TTS = 78 boundary risks; pure overhead | Medium |
| 8 | NCT trial updates flagged "new" when only the API timestamp changed | User flagged this evening | Medium |
| 9 | No quality measurement loop | No A/B, no listener feedback, no transcript-vs-script divergence metric | Medium |
| 10 | Scriptwriter ignores `config.CLAUDE_MODEL` env var (model hardcoded) | env var is dead code | Low |

---

## The plan: phased by risk + AATS timing

### Phase 0 — Tonight (in flight)
- ✅ Mainstream-press hierarchy in scriptwriter + weekly prompts
- ✅ Editor-curated featured-stories injection (`tasks/featured_<date>.md`)
- ✅ Music pre-normalize + stinger removal in assembler
- ✅ WAV-intermediate TTS, single MP3 encode at end
- ✅ Opus 4.7 for script + weekly
- 🟡 Re-render today's episode and ship to McKay

### Phase 1 — Sunday-Monday (T-3 to T-2). Safe pre-AATS wins.

**1A. Auphonic post-processing pipeline.** $0.50/episode, ~30 min integration.
- Sign up Auphonic, get API key
- New module `podcast/auphonic.py` — POST assembled MP3, poll for result, download cleaned MP3
- Auphonic does: loudness target (-16 LUFS for podcast), true-peak limiter (-1 dBTP), noise gate, leveler, optional EQ
- Replaces our amateur compress+normalize chain with a single API call
- Risk: low. If Auphonic returns bad audio, fall back to current MP3.

**1B. Switch script generation to Sonnet 4.6 (default; Opus on opt-in).**
- $0.15 per script (vs $1.40 on Opus) → 90%+ savings
- Read `config.CLAUDE_MODEL` env var properly (fix the dead code)
- Default: Sonnet. CI workflow can opt into Opus by setting env var when premium quality needed
- Frees budget for multi-pass workflow in Phase 2
- Risk: low. Sonnet 4.6 is well-suited to long-context structured generation

**1C. NCT trial-update dedup.** Track previous status per NCT ID; only surface real changes.
- Add `trial_status` table to dedup DB keyed by NCT ID
- On poll, compare current status to last known; only emit if changed (recruiting → active, completed, terminated)
- Cleans up "new updates" framing across daily/weekly/podcast
- Risk: low

**1D. REPAIR-MR / PRIMATY enrollment status fact-check.**
- Query ClinicalTrials.gov v2 API for current status of both
- Update the script's standing language about "active not yet recruiting" to match reality
- Risk: zero (fact-check only)

### Phase 2 — Wed-Fri (T-2 to launch). Editorial workflow.

**2A. Friday editor brief.** Highest-leverage process change you proposed.
- New cron: Friday 17:00 CT
- Generates `tasks/editor_brief_<saturday_date>.md` with:
  - Top 5 candidate stories ranked with rationale
  - Section-by-section content summary
  - Flagged paywalled articles needing user paste-in
  - Status changes from week (NCT updates, FDA actions, earnings)
- You edit the brief Friday night / Saturday morning
- Saturday's pipeline reads the brief as canonical input
- Risk: low — additive only, doesn't break existing flow

**2B. Weekly→Podcast transform (NOT parallel synthesis).**
- Podcast scriptwriter takes weekly HTML as PRIMARY input, not raw daily digests
- Eliminates duplicated editorial logic
- Weekly remains canonical; podcast is a downstream representation
- Could be deferred to post-AATS if risky
- Risk: medium — changes podcast input shape

### Phase 3 — Post-AATS (May+). TTS overhaul.

**3A. ElevenLabs TTS.** Will be the single biggest perceived-quality jump.
- ~$5/episode (vs $0.75 OpenAI) — 6.5x cost increase
- Voices: pick two reasonable ones for Nolan + Claire, or upload cloned voices
- Replaces synthesizer entirely; same WAV-intermediate output
- Risk: medium — need A/B testing, voice consistency week-to-week

**3B. Multi-pass script generation.**
- Pass 1 (Sonnet): outline + section bullets
- Pass 2 (Sonnet, per-section): write each section's dialogue with the outline as context
- Pass 3 (Opus): critique the assembled script for hallucinations, hierarchy, length
- Pass 4 (Sonnet): apply critique fixes
- Total cost: ~$0.50, dramatically more reliable than single-shot
- Risk: medium — more orchestration code

**3C. Mixed-mode hosting.** Editor records intro + outro + key transitions in own voice; TTS handles analysis sections.
- Most authentic option; ~10 min/week of recording
- Tooling: simple recording UI that auto-generates a "to record" list each week
- Risk: low (additive); high impact

### Phase 4 — Beyond. Architecture.

**4A. EZproxy / institutional auth integration.** Enables fetching paywalled WSJ/NYT/FT/Bloomberg directly. Per CLAUDE.md "Tier 4 post-launch" — was always planned.

**4B. Quality measurement loop.** Whisper transcript of published MP3 vs source script — divergence flags TTS errors. Listener feedback channel. Per-episode quality score over time.

**4C. Architectural: editor reviews script in a web UI.** Replace stdin pause with a small dashboard. Per-segment thumbs-up/edit/regenerate. Approve to publish.

---

## Cost projection per episode

| Pipeline | Script | TTS | Post | Total | Per-episode quality |
|---|---|---|---|---|---|
| **Current (post-tonight)** | $1.40 (Opus) | $0.75 (OpenAI WAV) | $0.00 | $2.15 | Acceptable |
| **End of Phase 1** | $0.15 (Sonnet) | $0.75 | $0.50 (Auphonic) | $1.40 | Significantly better |
| **End of Phase 3 (with ElevenLabs)** | $0.50 (multi-pass) | $5.00 (ElevenLabs) | $0.50 | $6.00 | Dramatically better |
| **With mixed-mode (editor records intros)** | $0.50 | $3.00 (less TTS) | $0.50 | $4.00 | Excellent |

For ~50 listeners/episode at launch, $6/episode is 12¢/listener. For 500 listeners (post-AATS growth target), 1.2¢/listener. Trivial.

---

## What this roadmap does NOT include

- Backwards re-mastering past episodes (templated rerender script exists; do per request)
- Sponsorship integration tooling
- Patreon / paid subscription gating
- Newsletter (Beehiiv) overhaul — separate concern

---

## Suggested execution sequence

1. **Tonight:** finish re-render, ship to McKay, sleep
2. **Sunday morning:** Phase 1A (Auphonic) + 1B (Sonnet)
3. **Sunday evening:** Phase 1C (trial dedup) + 1D (status fact-check)
4. **Tuesday:** Phase 2A (Friday editor brief tooling)
5. **Friday Apr 30 (T-1 from AATS Apr 29 — actually T+1; confirm):** First Friday editor brief, edit, Saturday auto-run uses it
6. **Post-AATS:** Phase 3 (ElevenLabs spike + multi-pass)

---

## Open questions for you

- **TTS choice:** ElevenLabs vs Cartesia vs mixed-mode (you record). Vote?
- **Auphonic vs build our own LUFS chain:** Auphonic is faster + better, but adds an external dependency. OK with that trade-off?
- **Cost ceiling per episode:** $6/episode acceptable? $10? More?
- **Two-host vs single-host:** Worth simplifying to monologue, or is the dynamic editorially valuable?
