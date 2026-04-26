# Podcast Pipeline Re-Engineering Roadmap

**Drafted:** 2026-04-25 (post-WSJ-rerender debug session)
**Constraint:** AATS launch 2026-04-29 (T-4 days). Don't break production before then.
**North star:** A podcast that doesn't sound like a robot reading a Claude script, with editorial gates that prevent missing front-page coverage of the field.

---

## Senior critique (Opus 4.7, 2026-04-25 session)

Honest assessment of where the current pipeline falls short, ranked by leverage.

### 1. The TTS choice is the floor on perceived quality
OpenAI TTS-1-HD ("fable", "nova") will always have telltale AI cadence, breathy artifacts, and occasional mispronunciations regardless of how clean the audio chain is. That's the actual ceiling. Real options: ElevenLabs (~$5/episode, dramatically more natural), Cartesia Sonic (fast, very good), Auphonic post-processing (~$0.50, fixes pydub's amateur output), or hiring a Fiverr/Voices.com VO actor for weekly recording (~$50-200, fully human, fully anonymous, best quality).

### 2. The pydub assembly chain is amateur-hour
The assembler had been clipping silently for 4+ weeks (April 4 episode = +1.16 dB peak). No LUFS measurement, no true-peak limiter, stacked compressors at default-tuned parameters. This is what professional podcast post-production tools (Auphonic, Adobe Podcast) do correctly out of the box for $0.50. Rolling our own audio engineering and it shows.

### 3. Script generation cost is upside-down
Paying ~$1.40 per script on Opus. Sonnet 4.6 would be ~$0.15 and probably 90% as good for this task. Bonus: cheaper script means a multi-pass workflow (outline → per-section → critique → final) becomes affordable. Single-shot 78-segment scripts are fragile; the WSJ-burial bug today was partly a "the model picked one ranking and you can't iterate cheaply" problem.

### 4. The two-host fiction added complexity for unclear payoff
78 segments × stitched TTS = 78 potential boundary artifacts, ~$0.75 in TTS, complex assembly logic, plus the "speaking back and forth is goofy" perception flagged by the editor. Single-host monologue is simpler, cheaper, and reads as more authoritative for medical content. **Decision: switch to single-host (executed 2026-04-25).**

### 5. No human-in-the-loop until publish
The pipeline auto-runs Saturday and ships. The Friday editor brief proposal is the highest-leverage process change. Even better long-term: editor approves the script every week (we built that gate today; should be permanent).

### 6. Architectural duplication between weekly + scriptwriter
Both have their own prompts, their own editorial stance text, both go back to raw daily digests. We had to add the mainstream-press hierarchy to BOTH this evening. They can disagree on framing. Should be: weekly is the canonical editorial output, podcast is a TRANSFORM of weekly (read the weekly, structure as monologue), not a parallel synthesis from the same raw data.

### 7. Source pipeline misses critical context
WSJ paywall blocked the pipeline from full text — caught only because the editor was a source for the article. The pipeline is currently blind to anything paywalled in major outlets. EZproxy integration ("Tier 4 post-launch" per CLAUDE.md) is the unlock. Until then, the Friday editor-brief gate compensates by letting the editor inject what was missed.

### 8. No quality measurement loop
No transcript diff against script (whisper hallucinates differently than the source script — a divergence metric would catch TTS errors). No A/B testing. No listener feedback. Every change today was based on "user listens, says scratchy, we guess." Not sustainable.

### Take if starting fresh with a 5x budget
- Sonnet for script, save the dollars
- ElevenLabs for voice (no editor voice — pen name discipline)
- Auphonic post-process the MP3
- Friday editor brief mandatory
- Weekly is canonical, podcast is a transform
- Single-host monologue (already decided)
- Budget ~$6-7/episode, dramatically better quality

The current pipeline is impressively complete for a side project, but it optimizes for "no human time" when the actual constraint is editorial quality and audio polish. ~30-45 min/week of editor time would be transformative — and the editor is currently spending way more than that fighting AI artifacts.

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

**3C. Voice strategy options (NO editor voice — pen name discipline forbids).**
Per CLAUDE.md hardwired privacy rule: editor never appears in any audio output.
Real options:
- ElevenLabs **library voice** (Adam, Bella, etc.) — anonymous, consistent, $5/ep
- ElevenLabs **instant voice clone of a different person with consent** — bespoke character voice, $5/ep
- **Hire a Fiverr or Voices.com VO actor** for weekly recording — $50-200/episode, fully human, fully anonymous, best quality. Two voices = $100-200/week.
- Stay on **OpenAI TTS-1-HD** — cheapest, current ceiling.

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
