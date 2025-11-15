"""Slug generation utilities for school identifiers."""

from __future__ import annotations

import re
import unicodedata

_NON_ALPHANUMERIC_RE = re.compile(r"[^a-z0-9]+")


def to_slug(name: str) -> str:
    """Convert an arbitrary school name into the canonical slug format."""
    if not name:
        return ""

    normalized = (
        unicodedata.normalize("NFKD", name)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    collapsed = _NON_ALPHANUMERIC_RE.sub("-", normalized)
    cleaned = collapsed.strip("-")
    return re.sub(r"-{2,}", "-", cleaned)


__all__ = ["to_slug"]
