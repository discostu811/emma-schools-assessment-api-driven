"""Deep Research pipeline that maintains the /raw files."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Iterable, Sequence

from emma_schools.config import School, load_dimensions
from emma_schools.core.paths import ensure_directories, raw_file
from emma_schools.deep_research import RAW_PROMPT_BUILDERS, run_deep_research

LOGGER = logging.getLogger(__name__)

SOURCE_START = "<!-- SOURCE-LOG:BEGIN -->"
SOURCE_END = "<!-- SOURCE-LOG:END -->"
FACT_START = "<!-- FACTS:BEGIN -->"
FACT_END = "<!-- FACTS:END -->"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_dimensions(dimensions: Sequence[str] | None) -> list[str]:
    if dimensions:
        return [dimension.lower() for dimension in dimensions]
    return load_dimensions()


def _raw_template(school: School, dimensions: Sequence[str]) -> str:
    categories = "\n".join(f"- {dimension}" for dimension in dimensions)
    return f"""# {school.name} — Raw Facts

## metadata
- slug: {school.slug}
- phase: {school.phase or 'n/a'}
- created: {_timestamp()}

## source-log
{SOURCE_START}
{SOURCE_END}

## categories
{categories}

## quoted-excerpts
<!-- QUOTES:BEGIN -->
<!-- QUOTES:END -->

## fact-records
{FACT_START}
{FACT_END}
"""


def _ensure_raw_file(school: School, dimensions: Sequence[str]) -> None:
    ensure_directories()
    path = raw_file(school.slug)
    if path.exists():
        return
    path.write_text(_raw_template(school, dimensions), encoding="utf-8")
    LOGGER.info("Created raw template for %s", school.name)


def _append_between_markers(path, start: str, end: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"({re.escape(start)})(.*?)(\s*{re.escape(end)})",
        flags=re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Markers {start} / {end} not found in {path}")

    existing = match.group(2).strip()
    addition = addition.strip()
    combined = addition if not existing else f"{existing}\n\n{addition}"
    replacement = f"{start}\n{combined}\n{end}"
    updated = text[: match.start()] + replacement + text[match.end() :]
    path.write_text(updated, encoding="utf-8")


def _set_between_markers(path, start: str, end: str, new_body: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(start)}.*?{re.escape(end)}",
        flags=re.DOTALL,
    )
    replacement = f"{start}\n{new_body.strip() if new_body.strip() else ''}\n{end}"
    updated = pattern.sub(replacement, text, count=1)
    path.write_text(updated, encoding="utf-8")


def _extract_sources(text: str) -> list[str]:
    sources = {
        match.group(1).strip()
        for match in re.finditer(r"-\s*Source:\s*(.+)", text)
        if match.group(1).strip()
    }
    return sorted(sources)


def _refresh_source_log(path) -> None:
    text = path.read_text(encoding="utf-8")
    sources = _extract_sources(text)
    body = "\n".join(f"- {source}" for source in sources)
    _set_between_markers(path, SOURCE_START, SOURCE_END, body)


def run_for_school_dimension(
    school: School,
    dimension: str,
    *,
    max_queries: int = 10,
    timeout: int = 600,
) -> None:
    dimension = dimension.lower()
    if dimension not in RAW_PROMPT_BUILDERS:
        raise ValueError(f"Unknown dimension: {dimension}")

    dimensions = _default_dimensions(None)
    _ensure_raw_file(school, dimensions)
    prompt_builder = RAW_PROMPT_BUILDERS[dimension]
    prompt = prompt_builder(school.name)
    topic = f"{school.name} — {dimension}"
    LOGGER.info("Running Deep Research | school=%s | dimension=%s", school.name, dimension)
    output = run_deep_research(
        topic=topic,
        instruction=prompt,
        max_queries=max_queries,
        timeout=timeout,
        school_name=school.name,
        dimension=dimension,
    )
    block = f"### Dimension Run: {dimension} — {_timestamp()}\n\n{output.strip()}\n"
    path = raw_file(school.slug)
    _append_between_markers(path, FACT_START, FACT_END, block)
    _refresh_source_log(path)
    LOGGER.info("Updated raw facts | school=%s | dimension=%s", school.name, dimension)


def run_for_school(
    school: School,
    dimensions: Sequence[str] | None = None,
) -> None:
    dims = _default_dimensions(dimensions)
    for dimension in dims:
        run_for_school_dimension(school, dimension)


def run_for_all(
    schools: Iterable[School],
    dimensions: Sequence[str] | None = None,
) -> None:
    dims = _default_dimensions(dimensions)
    for school in schools:
        for dimension in dims:
            run_for_school_dimension(school, dimension)


__all__ = ["run_for_school_dimension", "run_for_school", "run_for_all"]
