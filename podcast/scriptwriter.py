"""Generate a conversational podcast script from the weekly digest."""

from __future__ import annotations

import json
import logging
import re

from anthropic import Anthropic

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a podcast scriptwriter for "The Valve Wire Weekly" — a medical podcast \
covering transcatheter valve technology. You write natural, engaging dialogue between \
two expert co-hosts:

- **Nolan** (Host A): E. Nolan Beckett — the lead host, a structural heart specialist. \
Authoritative but approachable. Sets up topics, provides clinical context, asks probing questions.

- **Claire** (Host B): Claire — a cardiovascular market analyst and co-host. \
Warm, insightful, brings the industry/financial perspective. Reacts naturally, \
offers complementary analysis, occasionally pushes back or adds nuance.

Your scripts should sound like a REAL conversation between two smart people who \
genuinely enjoy discussing this topic — NOT like two people reading bullet points. \
Include:
- Natural transitions ("So Claire, turning to mitral...", "That's fascinating, Nolan...")
- Genuine reactions ("Wow, that's significant", "I didn't expect that")
- Occasional interruptions or building on each other's points
- Rhetorical questions to the audience
- Brief moments of humor or personality
- Each speaker turn should be 1-4 sentences (keep it conversational, not lecture-like)"""

SCRIPT_PROMPT = """\
Write a podcast script for "The Valve Wire Weekly" covering {start_date} through {end_date}.

The script should be 3,500-4,500 words total, targeting 15-20 minutes of audio.

## Output Format
Return a JSON array of script segments. Each segment is an object with:
- "speaker": "A" (Nolan) or "B" (Claire)
- "text": The spoken dialogue (1-4 sentences, MUST be under 3500 characters)
- "section": One of "intro", "top_stories", "aortic", "mitral", "tricuspid", \
"trials", "surgical_comparison", "market", "weekend", "closing"

Example format:
```json
[
  {{"speaker": "A", "text": "Welcome to The Valve Wire Weekly...", "section": "intro"}},
  {{"speaker": "B", "text": "Thanks Nolan. What a week...", "section": "intro"}}
]
```

## Script Structure
1. **Intro** (~1 min): Warm welcome, preview the week's biggest stories
2. **Top Stories** (~3 min): The 2-3 most impactful developments with analysis
3. **Aortic Valve** (~2-3 min): TAVR developments if any
4. **Mitral Valve** (~2-3 min): Repair and replacement developments
5. **Tricuspid Valve** (~2-3 min): Repair and replacement developments
6. **Clinical Trials** (~2-3 min): Key trial updates, landmark trial status
7. **Market & Industry** (~2-3 min): Stock performance, M&A, earnings — Claire leads this section
8. **Weekend News** (~1 min): Any weekend developments
9. **Closing** (~1 min): Key takeaways, what to watch next week, sign off

## Guidelines
- Reference specific studies, trials, and sources by name
- Mention specific numbers: enrollment figures, stock prices, percentage changes
- Nolan leads the clinical sections; Claire leads the market/industry section
- Both contribute to all sections with their respective expertise
- The sign-off should mention subscribing to The Valve Wire newsletter
- Make it sound like a real conversation — NOT a scripted reading

## Weekly Content
{weekly_content}

Return ONLY the JSON array. No other text."""


def generate_podcast_script(weekly_html: str, start_date: str = "", end_date: str = "") -> list[dict]:
    """Generate a conversational podcast script from the weekly digest.

    Args:
        weekly_html: The weekly digest HTML content.
        start_date: Start of the week (e.g., "March 9").
        end_date: End of the week (e.g., "March 14, 2026").

    Returns:
        List of script segment dicts with speaker, text, and section.
    """
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    prompt = SCRIPT_PROMPT.format(
        start_date=start_date or "this past week",
        end_date=end_date or "today",
        weekly_content=weekly_html,
    )

    logger.info(f"Generating podcast script with {config.CLAUDE_MODEL}")

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=16384,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text
    logger.info(
        f"Script generated: {len(raw)} chars, "
        f"tokens: {message.usage.input_tokens} in / {message.usage.output_tokens} out"
    )

    # Parse JSON from response (handle markdown code blocks)
    json_str = raw.strip()
    if json_str.startswith("```"):
        json_str = re.sub(r"^```(?:json)?\s*", "", json_str)
        json_str = re.sub(r"\s*```$", "", json_str)

    try:
        script = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse script JSON: {e}")
        logger.debug(f"Raw response: {raw[:500]}")
        raise

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

    logger.info(f"Script has {len(cleaned)} segments ({sum(len(s['text']) for s in cleaned)} chars total)")
    return cleaned
