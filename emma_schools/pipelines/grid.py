"""Generate the scoring grid Markdown from the CSV."""

from __future__ import annotations

import csv
import logging
import re
from typing import List

from emma_schools.core.paths import data_csv, scoring_grid
from emma_schools.core.slugs import to_slug
from emma_schools.pipelines.scoring import DIMENSION_HEADERS, SECTION_TITLES

LOGGER = logging.getLogger(__name__)

START_MARKER = "<!-- GRID:BEGIN -->"
END_MARKER = "<!-- GRID:END -->"


def _format_value(value: str | float, decimals: int) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    formatted = f"{number:.{decimals}f}"
    if decimals:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted


def _build_row(row: dict) -> str:
    school_name = row.get("School", "Unknown")
    slug = to_slug(school_name)
    overall = _format_value(row.get("Overall", "-"), 2)
    cells = [f"[{school_name}](/evidence/{slug})", f"[{overall}](/evidence/{slug})"]
    for dimension in DIMENSION_HEADERS:
        score = _format_value(row.get(dimension, "-"), 1)
        anchor = SECTION_TITLES.get(dimension, dimension.lower())
        cells.append(f"[{score}](/evidence/{slug}#{anchor})")
    return "| " + " | ".join(cells) + " |"


def _replace_grid(content: str, rows: List[str]) -> str:
    block = "\n".join(rows) if rows else ""
    replacement = f"{START_MARKER}\n{block}\n{END_MARKER}"
    pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        flags=re.DOTALL,
    )
    return pattern.sub(replacement, content)


def update_scoring_grid() -> None:
    csv_path = data_csv()
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing CSV file: {csv_path}")

    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    markdown_path = scoring_grid()
    if not markdown_path.exists():
        raise FileNotFoundError(f"Missing scoring grid file: {markdown_path}")

    new_rows = [_build_row(row) for row in rows]
    updated = _replace_grid(markdown_path.read_text(encoding="utf-8"), new_rows)
    markdown_path.write_text(updated, encoding="utf-8")
    LOGGER.info("Updated scoring grid with %s rows", len(new_rows))


__all__ = ["update_scoring_grid"]
