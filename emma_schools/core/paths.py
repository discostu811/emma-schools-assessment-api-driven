"""Helper functions for navigating the fixed repository layout."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "raw"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
LOGIC_DIR = PROJECT_ROOT / "logic"
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
SCORING_GRID_PATH = DOCS_DIR / "synthesis" / "scoring-grid.md"


def ensure_directories() -> None:
    """Create the required top-level directories if they do not exist."""
    for path in (RAW_DIR, EVIDENCE_DIR, LOGIC_DIR, DATA_DIR, DOCS_DIR / "synthesis"):
        path.mkdir(parents=True, exist_ok=True)


def raw_file(slug: str) -> Path:
    return RAW_DIR / f"{slug}-raw.md"


def evidence_file(slug: str) -> Path:
    return EVIDENCE_DIR / f"{slug}.md"


def data_csv() -> Path:
    return DATA_DIR / "schools.csv"


def scoring_grid() -> Path:
    return SCORING_GRID_PATH


__all__ = [
    "PROJECT_ROOT",
    "RAW_DIR",
    "EVIDENCE_DIR",
    "LOGIC_DIR",
    "DATA_DIR",
    "DOCS_DIR",
    "SCORING_GRID_PATH",
    "ensure_directories",
    "raw_file",
    "evidence_file",
    "data_csv",
    "scoring_grid",
]
