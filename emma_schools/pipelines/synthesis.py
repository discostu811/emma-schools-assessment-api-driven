"""Convert raw facts into structured evidence files."""

from __future__ import annotations

import logging
from typing import Iterable

from emma_schools.config import School
from emma_schools.core.paths import evidence_file, raw_file
from emma_schools.deep_research import evidence_prompt, run_chat_completion

LOGGER = logging.getLogger(__name__)

EVIDENCE_SECTIONS = [
    "academics",
    "arts",
    "facilities",
    "pastoral",
    "commute",
    "reputation",
    "fit",
]


def _normalize_output(school_name: str, text: str) -> str:
    text = text.strip()
    if not text.startswith("#"):
        text = f"# {school_name} — Evidence\n\n{text}"
    for section in EVIDENCE_SECTIONS:
        header = f"## {section}"
        if header not in text:
            text += f"\n\n{header}\n"
    return text.strip() + "\n"


def build_evidence_for_school(
    school: School,
    *,
    model: str | None = None,
) -> str:
    raw_path = raw_file(school.slug)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw file missing for {school.name}: {raw_path}")

    prompt = evidence_prompt(school.name, raw_path.read_text(encoding="utf-8"))
    messages = [
        {
            "role": "system",
            "content": "You are a careful research editor. Output Markdown that follows instructions exactly.",
        },
        {"role": "user", "content": prompt},
    ]
    LOGGER.info("Building evidence for %s", school.name)
    output = run_chat_completion(messages, model=model)
    normalized = _normalize_output(school.name, output)
    path = evidence_file(school.slug)
    path.write_text(normalized, encoding="utf-8")
    LOGGER.info("Wrote evidence file %s", path)
    return normalized


def build_evidence_for_all(
    schools: Iterable[School],
    *,
    model: str | None = None,
) -> None:
    for school in schools:
        try:
            build_evidence_for_school(school, model=model)
        except FileNotFoundError as exc:
            LOGGER.warning(str(exc))


__all__ = ["build_evidence_for_school", "build_evidence_for_all", "EVIDENCE_SECTIONS"]
