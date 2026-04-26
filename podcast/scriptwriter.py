"""Generate a conversational podcast script from the weekly digest."""

from __future__ import annotations

import json
import logging
import re

from anthropic import Anthropic

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a scriptwriter for "The Valve Wire Weekly" — a medical podcast covering \
transcatheter valve technology. You write a SINGLE-HOST monologue script delivered \
by E. Nolan Beckett, MD — a structural heart specialist and cardiothoracic surgeon.

Voice and tone:
- Authoritative, analytical, dry — not chatty. The host is a senior surgeon, not a radio personality.
- Direct address to the listener: "this week", "here's why this matters", "the data show"
- No co-host, no dialogue, no rhetorical "now Claire" or "as we said earlier"
- Sentences vary in length but skew tight — this is a written essay read aloud, not improvised conversation
- Confidence without bombast. Skepticism without snark.
- Comfortable with technical density; assumes a clinical or pharma-fluent listener

## CRITICAL EDITORIAL STANCE
Many structural heart technologies have gotten ahead of the science and clinical \
guidelines. This podcast must be BALANCED and CIRCUMSPECT:
- Always present BOTH sides: favorable findings AND limitations/criticisms
- Flag study design weaknesses: Was it randomized? Prospective? Industry-sponsored? \
Short follow-up? Small sample size? Single-center?
- When discussing favorable transcatheter outcomes, also note surgical alternatives, \
durability concerns, patient selection biases, and complication rates
- Reference critical perspectives from authors like Bowdish, Badhwar, Mehaffey, Kaul, \
Miller, and Chikwe who have published on therapies getting ahead of evidence
- Never present transcatheter superiority as settled when long-term data is lacking \
or guidelines don't yet support broad adoption
- Use phrases like "the long-term data still isn't there", "this was a single-center \
retrospective study", "we need to be careful here", "this is hypothesis-generating, \
not practice-changing"
- Where industry enthusiasm may outpace evidence (earnings beats, stock movements, \
analyst upgrades), name the gap explicitly

The tone is expert skepticism — informed, analytical, enthusiastic about real advances \
but always questioning. Think peer review, not press release. Think a senior surgeon \
recording a 25-minute briefing for colleagues, not two people on a podcast set."""

SCRIPT_PROMPT = """\
Write a podcast script for "The Valve Wire Weekly" {episode_label}covering {start_date} \
through {end_date}.

The script must be 3,000-4,000 words total — hard maximum 4,000 words (20 minutes at conversational pace). \
Be comprehensive but tight. Every sentence must earn its place. No padding, no repetition, no lengthy transitions. \
Cover the week's most important developments with sharp clinical commentary. Quality over quantity.

## Output Format
Return a JSON array of script segments. Each segment is an object with:
- "speaker": always "A" (this is a single-host monologue — no co-host)
- "text": A paragraph the host reads aloud (1-5 sentences, MUST be under 3500 characters). \
Segment boundaries should fall at natural pauses (end of paragraph, end of subtopic) — \
NOT mid-thought.
- "section": One of "intro", "disclaimer", "meeting_highlights", "top_stories", \
"aortic", "mitral", "tricuspid", "trials", "surgical_comparison", "market", \
"weekend", "closing"

Example format:
```json
[
  {{"speaker": "A", "text": "Welcome to The Valve Wire Weekly for the week ending [date]. Today's headlines: [headline 1]. [headline 2]. [headline 3].", "section": "intro"}},
  {{"speaker": "A", "text": "Before we dive in, a quick reminder — this podcast is for educational and informational purposes only. Nothing we discuss should be taken as medical advice.", "section": "disclaimer"}}
]
```

## Script Structure
1. **Intro** (~30-45 sec, 3-5 segments): Brief welcome, then a tight headline list of \
the week's top 4-6 stories. NOT a conversational lead-in. Format: "Welcome to The Valve \
Wire Weekly for the week ending [date]. Here's what we're covering today." Then one \
segment per headline (1-2 sentences each, name the actual topic, no teaser language). \
Close with "Let's get into it."
2. **Disclaimer** (~15 sec, 1 segment): Brief medical disclaimer: "Before we dive in, \
a quick reminder — this podcast is for educational and informational purposes only. \
Nothing we discuss should be taken as medical advice. Always consult your physician or \
care team for clinical decisions."
{meeting_section}\
3. **Top Stories** (~5-7 min): The 3-5 most impactful developments with sharp analysis
4. **Aortic Valve** (~2 min): TAVR — top findings only, skip minor updates
5. **Mitral Valve** (~2 min): Repair and replacement — top findings only
6. **Tricuspid Valve** (~1-2 min): Top findings only, omit if light week
7. **Clinical Trials** (~1-2 min): Notable status changes only, not every trial
8. **Market & Industry** (~2 min): Stock performance, M&A, earnings
9. **Weekend News** (~30 sec): Only if genuinely newsworthy
10. **Closing** (~1 min): 2-3 key takeaways, what to watch, sign off

Keep each section tight. If a section has nothing significant, compress or skip it rather than padding.

## Journal Hierarchy (PRIORITIZE in this order)
When selecting which stories to emphasize, prioritize findings from higher-impact journals:
NEJM > JAMA > JACC > Lancet > EHJ > JACC:CI > surgical journals (ATS, JTCVS, EJCTS)
An NEJM or JAMA publication should ALWAYS be a top story. Name the journal when citing.

## Mainstream Media Hierarchy (PRIORITIZE — this is non-negotiable)
When a major mainstream outlet publishes a feature or front-page article on \
transcatheter or surgical valve technology, that IS a top story regardless of \
whether a peer-reviewed publication accompanies it. Mainstream coverage shapes \
patient inquiries, referring-physician perception, payer attention, and policy. \
You MUST lead with these in the Top Stories section, dedicate substantive \
discussion to their framing and fairness, and never bury them mid-section.

Outlets that meet this bar:
- Wall Street Journal (especially front-page or section-front)
- New York Times
- Washington Post
- Financial Times
- Bloomberg (terminal stories or Businessweek features)
- Reuters and Associated Press national wire stories
- The Economist
- Major TV networks (CBS, NBC, ABC, CNN, FOX, BBC) news segments

When a WSJ or NYT piece appears alongside an industry earnings beat or a \
clinical study, treat the tension between mainstream skepticism and commercial/ \
clinical momentum as the central narrative, not as competing items in a list.

## Accuracy Safeguards (CRITICAL)
- ONLY cite specific numbers, percentages, and enrollment figures that appear in the \
weekly content below. If you cannot find a specific number, use qualitative language \
("significant improvement", "substantial reduction") rather than inventing a number.
- NEVER attribute a study to a journal unless that journal's name appears in the source material.
- NEVER invent author names. Only mention authors whose names appear in the source content \
or in the editorial stance instructions above.
- When discussing study findings, state the study design if known (randomized, registry, \
single-center, retrospective). If the design is not mentioned in the source, do not guess.

## Guidelines
- Reference specific studies, trials, and sources by name when they appear in the source
- Mention specific numbers ONLY when they are in the source material
- This is a single-host monologue — never use phrases like "as my co-host noted" or "now turning to you"
- The sign-off should mention subscribing to The Valve Wire newsletter
- Read like a polished essay, not casual conversation. The host wrote it down before recording.

## Pronunciation Guide (IMPORTANT — spell these out in the script)
- TAVR → write as "TAVR" (rhymes with "saver", the TTS will handle it)
- TAVI → write as "tah-vee"
- TMVR → write as "T-M-V-R" (spell out each letter)
- TTVR → write as "T-T-V-R" (spell out each letter)
- SAVR → write as "saver" or "surgical aortic valve replacement"
- MitraClip → write as "Mitra-Clip"
- TriClip → write as "Try-Clip"
- PASCAL → write as "Pascal"
- Tendyne → write as "Ten-dine"
- Intrepid → write as "Intrepid"
- Evoque → write as "Eh-voke"
- SAPIEN → write as "Say-pee-en"
- CoreValve → write as "Core-Valve"
- Evolut → write as "Ev-oh-loot"
- COAPT → write as "co-apt"
- Beehiiv → write as "Bee-hive"
- NCT → write as "N-C-T"
- EW → write as "Edwards Lifesciences" (never say "E-W")
- MDT → write as "Medtronic"
- ABT → write as "Abbott"
- BSX → write as "Boston Scientific"
- P/E → write as "P-E ratio" or "price to earnings"
- ClinicalTrials.gov → write as "clinicaltrials dot gov"
- NEJM → write as "The New England Journal of Medicine" or "N-E-J-M"
- JACC → write as "Jack" (this is how cardiologists say it)
- For any medical acronym not listed, spell out the full name on first use

## Weekly Content
{weekly_content}

Return ONLY the JSON array. No other text."""


def _format_article_metadata_for_prompt(article_metadata: list[dict]) -> str:
    """Format structured article metadata as a reference section for the prompt."""
    if not article_metadata:
        return ""

    # Only include articles that have meaningful data
    useful = [
        a for a in article_metadata
        if a.get("title") and (a.get("key_finding") or a.get("key_numbers"))
    ]
    if not useful:
        return ""

    lines = [
        "\n## Verified Article Data (USE THESE as ground truth)",
        "The following are verified facts from this week's articles. When discussing",
        "these studies, use ONLY the numbers and attributions listed here:\n",
    ]

    for a in useful:
        parts = [f"- **{a['title']}**"]
        if a.get("journal"):
            parts.append(f"  Journal: {a['journal']}")
        if a.get("authors"):
            parts.append(f"  Authors: {a['authors']}")
        if a.get("study_design"):
            parts.append(f"  Design: {a['study_design']}")
        if a.get("sample_size"):
            parts.append(f"  Sample size: {a['sample_size']}")
        if a.get("key_finding"):
            parts.append(f"  Key finding: {a['key_finding']}")
        if a.get("key_numbers"):
            parts.append(f"  Key numbers: {', '.join(a['key_numbers'])}")
        if a.get("url"):
            parts.append(f"  URL: {a['url']}")
        lines.append("\n".join(parts))

    return "\n\n".join(lines)


def generate_podcast_script(
    weekly_html: str,
    start_date: str = "",
    end_date: str = "",
    episode_number: int = None,
    article_metadata: list[dict] = None,
) -> list[dict]:
    """Generate a conversational podcast script from the weekly digest.

    Args:
        weekly_html: The weekly digest HTML content.
        start_date: Start of the week (e.g., "March 9").
        end_date: End of the week (e.g., "March 14, 2026").
        episode_number: Episode number for the intro (e.g., 12).
        article_metadata: Optional structured article data from daily sidecars.

    Returns:
        List of script segment dicts with speaker, text, and section.
    """
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    episode_label = f"— Episode {episode_number} — " if episode_number else ""
    episode_intro_note = (
        f". Nolan should mention this is episode {episode_number}"
        if episode_number else ""
    )

    logger.info("Generating podcast script with claude-opus-4-7")

    # Check for active/recent meetings first — affects prompt structure (R6)
    from datetime import date as _date, timedelta as _td
    from processing.summarizer import _get_active_meeting_context, MAJOR_MEETINGS
    _today = _date.today()
    _meeting_context = _get_active_meeting_context(_today)
    _meeting_name = None
    if not _meeting_context:
        for _d in range(1, 8):
            _meeting_context = _get_active_meeting_context(_today - _td(days=_d))
            if _meeting_context:
                _meeting_context = _meeting_context.replace(
                    "is currently taking place",
                    "took place this past week"
                ) + (
                    "\n\nIMPORTANT: Dedicate a significant portion of this podcast to "
                    "summarizing the key presentations, late-breaking trials, and "
                    "newsworthy announcements from this meeting. This should be a "
                    "major segment, not a brief mention."
                )
                # Extract meeting name for section header
                for name, _month, _day, _dur in MAJOR_MEETINGS:
                    if name in _meeting_context:
                        _meeting_name = name
                        break
                break

    # Build meeting highlights section for script structure (R6)
    if _meeting_name:
        meeting_section = (
            f'2b. **{_meeting_name} Highlights** (~5-7 min, section="meeting_highlights"): '
            f"Dedicated segment covering the key presentations, late-breaking trials, "
            f"and major announcements from {_meeting_name}. This is the centerpiece of "
            f"the episode. Discuss the most impactful presentations in order of clinical "
            f"significance. Cover both clinical implications and industry/market reactions.\n"
        )
    else:
        meeting_section = ""

    prompt = SCRIPT_PROMPT.format(
        start_date=start_date or "this past week",
        end_date=end_date or "today",
        weekly_content=weekly_html,
        episode_label=episode_label,
        episode_intro_note=episode_intro_note,
        meeting_section=meeting_section,
    )

    # Append verified article metadata if available
    metadata_section = _format_article_metadata_for_prompt(article_metadata)
    if metadata_section:
        prompt = prompt.replace(
            "Return ONLY the JSON array. No other text.",
            metadata_section + "\n\nReturn ONLY the JSON array. No other text.",
        )
        logger.info(f"Appended {len(article_metadata)} article metadata records to prompt")

    # Inject guidelines knowledge into the system prompt
    from knowledge import get_full_knowledge_context
    knowledge = get_full_knowledge_context()
    system_with_knowledge = SYSTEM_PROMPT
    if _meeting_context:
        system_with_knowledge += "\n\n" + _meeting_context
        logger.info("Meeting context injected into podcast prompt")
    if knowledge:
        system_with_knowledge += "\n\n" + knowledge
        logger.info(f"Injected {len(knowledge)} chars of guidelines context")

    # Generate script with retry on JSON parse failure (R7, R8)
    script = None
    for attempt in range(2):
        extra_instruction = ""
        if attempt > 0:
            extra_instruction = (
                "\n\nIMPORTANT: Your previous response was not valid JSON. "
                "Return ONLY a valid JSON array. No trailing commas, no unescaped "
                "quotes, no text outside the array."
            )
            logger.warning("Retrying script generation after JSON parse failure")

        message = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=16384,
            system=system_with_knowledge,
            messages=[{"role": "user", "content": prompt + extra_instruction}],
            timeout=21600.0,
        )

        raw = message.content[0].text
        logger.info(
            f"Script generated (attempt {attempt + 1}): {len(raw)} chars, "
            f"tokens: {message.usage.input_tokens} in / {message.usage.output_tokens} out"
        )

        # Parse JSON from response (handle markdown code blocks)
        json_str = raw.strip()
        if json_str.startswith("```"):
            json_str = re.sub(r"^```(?:json)?\s*", "", json_str)
            json_str = re.sub(r"\s*```$", "", json_str)

        try:
            script = json.loads(json_str)
            break  # Success
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse script JSON (attempt {attempt + 1}): {e}")
            logger.debug(f"Raw response: {raw[:500]}")
            if attempt == 1:
                raise  # Final attempt, propagate error

    # Validate and clean
    valid_speakers = {"A", "B"}
    cleaned = []
    for i, seg in enumerate(script):
        if seg.get("speaker") not in valid_speakers:
            logger.warning(f"Segment {i} has invalid speaker: {seg.get('speaker')}")
            continue
        text = seg.get("text", "").strip()
        if not text:
            continue
        if len(text) > 3500:
            logger.warning(f"Segment {i} too long ({len(text)} chars), truncating")
            text = text[:3500]
        cleaned.append({
            "speaker": seg["speaker"],
            "text": text,
            "section": seg.get("section", ""),
        })

    # Validate total word count (R4)
    total_words = sum(len(s["text"].split()) for s in cleaned)
    if total_words < 2500:
        logger.warning(f"Script is short: {total_words} words (target: 3,000-4,000)")
    elif total_words > 4000:
        logger.warning(f"Script exceeds 20-min limit: {total_words} words — trimming to 4,000")
        # Hard trim: drop segments from the end (before closing) until under 4,000 words
        closing = [s for s in cleaned if s.get("section") == "closing"]
        body = [s for s in cleaned if s.get("section") != "closing"]
        trimmed = []
        word_count = 0
        closing_words = sum(len(s["text"].split()) for s in closing)
        budget = 4000 - closing_words
        for seg in body:
            seg_words = len(seg["text"].split())
            if word_count + seg_words <= budget:
                trimmed.append(seg)
                word_count += seg_words
            else:
                break
        cleaned = trimmed + closing
        final_words = sum(len(s["text"].split()) for s in cleaned)
        logger.info(f"Trimmed script to {final_words} words ({len(cleaned)} segments)")

    # Validate required sections are present
    required_sections = {"intro", "top_stories", "closing"}
    found_sections = {s["section"] for s in cleaned}
    missing = required_sections - found_sections
    if missing:
        logger.warning(f"Script missing required sections: {missing}")

    # Hallucination check: flag study references not found in source material (R4)
    _validate_references(cleaned, weekly_html, article_metadata=article_metadata)

    logger.info(f"Script has {len(cleaned)} segments ({sum(len(s['text']) for s in cleaned)} chars total)")
    return cleaned


def _validate_references(
    script: list[dict],
    source_html: str,
    article_metadata: list[dict] = None,
) -> None:
    """Check that study/trial names, numbers, and journals in the script appear in sources.

    Logs warnings for any references that appear fabricated. Does not block generation
    — this is a quality signal, not a gate.
    """
    if not source_html:
        return

    source_lower = source_html.lower()
    all_text = " ".join(s["text"] for s in script)

    # Build a combined reference corpus from source HTML + metadata
    metadata_text = ""
    metadata_numbers = set()
    metadata_journals = set()
    if article_metadata:
        for a in article_metadata:
            metadata_text += " " + a.get("title", "") + " " + a.get("key_finding", "")
            for n in a.get("key_numbers", []):
                metadata_numbers.add(n.strip())
            if a.get("journal"):
                metadata_journals.add(a["journal"].lower().strip())
    combined_lower = source_lower + " " + metadata_text.lower()

    # --- 1. Study name validation (existing) ---
    study_patterns = re.findall(
        r'(?:the\s+)?([A-Z][A-Z0-9-]{2,})\s+(?:trial|study|registry|data|results|findings)',
        all_text,
    )

    skip_words = {
        "THE", "AND", "FOR", "BUT", "NOT", "THIS", "THAT", "WITH", "TAVR",
        "TAVI", "TMVR", "TTVR", "SAVR", "FDA", "CMS", "ACC", "AHA", "ESC",
        "EACTS", "TCT", "STS", "AATS", "TTS", "RSS", "CEO", "CFO",
    }

    flagged_studies = []
    for study in study_patterns:
        if study in skip_words:
            continue
        if study.lower() not in combined_lower:
            flagged_studies.append(study)

    if flagged_studies:
        logger.warning(
            f"HALLUCINATION CHECK: {len(flagged_studies)} study reference(s) not found "
            f"in source material: {', '.join(flagged_studies)}. These may be fabricated "
            f"or from the knowledge base. Review before publishing."
        )

    # --- 2. Percentage validation ---
    # Extract percentages from the script (e.g., "42.3%", "a 15% reduction")
    script_percentages = re.findall(r'(\d+\.?\d*)\s*%', all_text)
    flagged_pct = []
    for pct in script_percentages:
        pct_str = pct + "%"
        pct_with_space = pct + " %"
        # Check in source HTML, metadata numbers, and metadata text
        found = (
            pct_str in source_html
            or pct_with_space in source_html
            or pct_str in metadata_text
            or any(pct in n for n in metadata_numbers)
        )
        if not found:
            flagged_pct.append(pct_str)

    if flagged_pct:
        # Deduplicate
        unique_pct = sorted(set(flagged_pct))
        logger.warning(
            f"ACCURACY CHECK: {len(unique_pct)} percentage(s) in script not found in "
            f"source material: {', '.join(unique_pct)}. Verify these are not fabricated."
        )

    # --- 3. Journal name validation ---
    # Look for "published in JOURNAL", "JOURNAL study", "in the JOURNAL" patterns
    journal_mentions = re.findall(
        r'(?:published in|in the|from the|reported in|in)\s+'
        r'((?:New England Journal of Medicine|NEJM|JAMA|JACC|Lancet|'
        r'European Heart Journal|EHJ|Circulation|Annals of Thoracic Surgery|'
        r'JTCVS|EJCTS|Journal of the American College of Cardiology|'
        r'Heart|BMJ|Nature Medicine|Structural Heart|'
        r'Journal of Thoracic and Cardiovascular Surgery|'
        r'European Journal of Cardio-Thoracic Surgery))',
        all_text,
        re.IGNORECASE,
    )

    flagged_journals = []
    for journal in journal_mentions:
        j_lower = journal.lower().strip()
        # Check source HTML and metadata
        if j_lower not in source_lower and j_lower not in metadata_journals:
            # Also check common abbreviation mappings
            abbrev_map = {
                "nejm": "new england journal",
                "jacc": "journal of the american college of cardiology",
                "ehj": "european heart journal",
                "jtcvs": "journal of thoracic and cardiovascular surgery",
                "ejcts": "european journal of cardio-thoracic surgery",
            }
            expanded = abbrev_map.get(j_lower, "")
            if not expanded or (expanded not in source_lower and expanded not in " ".join(metadata_journals)):
                flagged_journals.append(journal)

    if flagged_journals:
        unique_journals = sorted(set(flagged_journals))
        logger.warning(
            f"ACCURACY CHECK: {len(unique_journals)} journal attribution(s) in script "
            f"not found in source material: {', '.join(unique_journals)}. "
            f"Verify these studies were actually published in these journals."
        )

    # --- 4. Numerical claims validation (enrollment, p-values, ratios) ---
    if article_metadata:
        # Extract specific numerical claims from script
        # P-values
        script_pvalues = re.findall(r'[Pp]\s*[<>=]\s*(0?\.\d+)', all_text)
        flagged_pvals = []
        for pv in script_pvalues:
            found = pv in source_html or any(pv in n for n in metadata_numbers)
            if not found:
                flagged_pvals.append(f"p={pv}")

        if flagged_pvals:
            logger.warning(
                f"ACCURACY CHECK: {len(flagged_pvals)} p-value(s) in script not found "
                f"in source material: {', '.join(flagged_pvals)}. "
                f"These may be fabricated."
            )

        # Enrollment / sample size numbers ("enrolled 500", "500 patients")
        script_enrollment = re.findall(
            r'(?:enrolled|included|randomized)\s+([\d,]+)\s*(?:patients|subjects|participants)',
            all_text, re.IGNORECASE,
        )
        metadata_sizes = {
            str(a["sample_size"]) for a in article_metadata
            if a.get("sample_size")
        }

        flagged_enrollment = []
        for n in script_enrollment:
            n_clean = n.replace(",", "")
            if n_clean not in source_html.replace(",", "") and n_clean not in metadata_sizes:
                flagged_enrollment.append(n)

        if flagged_enrollment:
            logger.warning(
                f"ACCURACY CHECK: {len(flagged_enrollment)} enrollment number(s) in "
                f"script not found in source material: {', '.join(flagged_enrollment)}. "
                f"Verify these sample sizes."
            )
