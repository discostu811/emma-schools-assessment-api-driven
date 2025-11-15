"""Evidence-to-score pipeline."""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import Dict, Iterable, List

from emma_schools.config import School
from emma_schools.core.paths import data_csv, evidence_file, ensure_directories

LOGGER = logging.getLogger(__name__)

DIMENSION_HEADERS = [
    "Academics",
    "Arts",
    "Facilities",
    "Pastoral",
    "Commute",
    "Reputation",
    "Fit",
]

SECTION_TITLES = {
    "Academics": "academics",
    "Arts": "arts",
    "Facilities": "facilities",
    "Pastoral": "pastoral",
    "Commute": "commute",
    "Reputation": "reputation",
    "Fit": "fit",
}

WEIGHTS = {
    "Academics": 0.25,
    "Arts": 0.15,
    "Facilities": 0.05,
    "Pastoral": 0.10,
    "Commute": 0.15,
    "Reputation": 0.10,
    "Fit": 0.20,
}

POSITIVE_KEYWORDS = [
    "excellent",
    "strong",
    "outstanding",
    "award",
    "scholar",
    "improved",
    "improving",
    "leading",
    "top",
    "high",
    "notable",
]

NEGATIVE_KEYWORDS = [
    "concern",
    "weak",
    "decline",
    "issue",
    "warning",
    "limited",
    "below",
    "poor",
    "criticism",
    "challenge",
]


def _extract_section(text: str, section: str) -> str:
    pattern = rf"##\s+{re.escape(section)}\s*(.*?)(?=\n## |\Z)"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _score_section(text: str) -> float:
    if not text.strip():
        return 1.0
    bullets = [line.strip() for line in text.splitlines() if line.strip().startswith("-")]
    detail_bonus = min(0.5, 0.05 * len(bullets))
    lower = text.lower()
    positives = sum(lower.count(keyword) for keyword in POSITIVE_KEYWORDS)
    negatives = sum(lower.count(keyword) for keyword in NEGATIVE_KEYWORDS)
    score = 3.0 + 0.25 * positives - 0.25 * negatives + detail_bonus
    return max(1.0, min(5.0, score))


def _parse_school_name(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            line = line.lstrip("#").strip()
            return line.split(" — ")[0]
    return "Unknown School"


def score_school(school: School) -> Dict[str, float | str]:
    path = evidence_file(school.slug)
    if not path.exists():
        raise FileNotFoundError(f"Evidence file missing for {school.name}: {path}")

    text = path.read_text(encoding="utf-8")
    name = _parse_school_name(text)
    section_scores = {
        dimension: _score_section(_extract_section(text, SECTION_TITLES[dimension]))
        for dimension in DIMENSION_HEADERS
    }

    overall = sum(section_scores[dim] * WEIGHTS[dim] for dim in DIMENSION_HEADERS)

    return {
        "School": name or school.name,
        "Slug": school.slug,
        **section_scores,
        "Overall": round(overall, 2),
    }


def score_all(schools: Iterable[School]) -> List[Dict[str, float | str]]:
    ensure_directories()
    rows: List[Dict[str, float | str]] = []
    for school in schools:
        try:
            score_row = score_school(school)
            rows.append(score_row)
            LOGGER.info("Scored %s", school.name)
        except FileNotFoundError as exc:
            LOGGER.warning(str(exc))

    if not rows:
        LOGGER.warning("No evidence files found; skipping CSV generation.")
        return rows

    rows.sort(key=lambda row: row["Overall"], reverse=True)
    header = ["School", "Overall", *DIMENSION_HEADERS]
    csv_path = data_csv()
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in header})

    LOGGER.info("Wrote %s", csv_path)
    return rows


__all__ = ["score_school", "score_all", "DIMENSION_HEADERS", "SECTION_TITLES"]
