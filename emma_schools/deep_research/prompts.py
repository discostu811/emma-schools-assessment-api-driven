"""Prompt builders for Deep Research and synthesis tasks."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Dict

FACT_RECORD_TEMPLATE = """\
### Fact ID: <dimension>-<increment>
- Category: <category>
- Tags: [tag1, tag2]
- Fact: <single factual statement>
- Quote: "<optional quote ≤ 25 words>"
- Source: <publication + URL>
- Accessed: YYYY-MM-DD
- Reliability: 1|2|3
- Notes: <optional context>
"""

DIMENSION_FOCUS = {
    "academics": (
        "curriculum, exam outcomes, value-add, inspections, destinations, selection "
        "policies, SEN/stretch provision, notable academic awards"
    ),
    "arts": (
        "music, drama, dance, fine art, performance facilities, notable productions, "
        "competitions, scholarships, visiting practitioners"
    ),
    "facilities": (
        "campus, buildings, labs, sports venues, music/drama spaces, recent refurbishments, "
        "shared/leased spaces, capacity constraints, capital projects"
    ),
    "pastoral": (
        "safeguarding, wellbeing, tutor systems, counselling, diversity & inclusion, "
        "behaviour, anti-bullying outcomes, partnerships, culture indicators"
    ),
    "commute": (
        "travel routes from Chiswick W4, public transport, school buses, journey times, "
        "safe cycling/walking, before/after-school logistics"
    ),
    "reputation": (
        "press coverage, awards, inspection accolades, parent/community sentiment, "
        "university destinations, league table positions"
    ),
    "fit": (
        "culture, ethos, student profile, co/extra-curricular breadth, scale, "
        "house/mentor structures, alignment with Emma's interests"
    ),
}


def _base_raw_prompt(school_name: str, dimension: str, focus: str) -> str:
    today = datetime.utcnow().date().isoformat()
    return f"""
You are performing deep desk research on **{school_name}** (secondary school in/near London).

DIMENSION: **{dimension.upper()}**
FOCUS: {focus}

TASK:
- Collect ONLY verifiable facts published on or before {today}.
- Use the atomic fact format EXACTLY for every fact:

{FACT_RECORD_TEMPLATE}

RULES:
- Cite the original source with publication name + URL and include accessed dates.
- Each quote ≤ 25 words.
- No opinions, no recommendations.
- Summarise only when multiple sources align and cite all sources used.
- Include enough metadata to relocate every source.
"""


def raw_prompt_academics(school_name: str) -> str:
    return _base_raw_prompt(school_name, "academics", DIMENSION_FOCUS["academics"])


def raw_prompt_arts(school_name: str) -> str:
    return _base_raw_prompt(school_name, "arts", DIMENSION_FOCUS["arts"])


def raw_prompt_facilities(school_name: str) -> str:
    return _base_raw_prompt(school_name, "facilities", DIMENSION_FOCUS["facilities"])


def raw_prompt_pastoral(school_name: str) -> str:
    return _base_raw_prompt(school_name, "pastoral", DIMENSION_FOCUS["pastoral"])


def raw_prompt_commute(school_name: str) -> str:
    return _base_raw_prompt(school_name, "commute", DIMENSION_FOCUS["commute"])


def raw_prompt_reputation(school_name: str) -> str:
    return _base_raw_prompt(school_name, "reputation", DIMENSION_FOCUS["reputation"])


def raw_prompt_fit(school_name: str) -> str:
    return _base_raw_prompt(school_name, "fit", DIMENSION_FOCUS["fit"])


RAW_PROMPT_BUILDERS: Dict[str, Callable[[str], str]] = {
    "academics": raw_prompt_academics,
    "arts": raw_prompt_arts,
    "facilities": raw_prompt_facilities,
    "pastoral": raw_prompt_pastoral,
    "commute": raw_prompt_commute,
    "reputation": raw_prompt_reputation,
    "fit": raw_prompt_fit,
}


def evidence_prompt(school_name: str, raw_text: str) -> str:
    """Create the synthesis prompt for transforming raw facts into evidence."""

    return f"""
You are synthesising the RAW FACTS for **{school_name}** into structured evidence.

RULES:
- Follow the template exactly:

# {school_name} — Evidence

## academics
## arts
## facilities
## pastoral
## commute
## reputation
## fit

- Each section: 5–15 factual bullet points derived strictly from the raw facts.
- Include short quotes ≤25 words with source + accessed date when helpful.
- No scoring, no recommendations, no speculation.
- Preserve explicit references to sources/dates.

RAW FACTS BELOW (do not quote verbatim unless in a short quote):

\"\"\"{raw_text}\"\"\"
"""


__all__ = [
    "FACT_RECORD_TEMPLATE",
    "DIMENSION_FOCUS",
    "RAW_PROMPT_BUILDERS",
    "raw_prompt_academics",
    "raw_prompt_arts",
    "raw_prompt_facilities",
    "raw_prompt_pastoral",
    "raw_prompt_commute",
    "raw_prompt_reputation",
    "raw_prompt_fit",
    "evidence_prompt",
]
