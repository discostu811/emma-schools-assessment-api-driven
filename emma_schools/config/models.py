"""Data models for configuration objects."""

from __future__ import annotations

from dataclasses import dataclass

from emma_schools.core.slugs import to_slug


@dataclass(slots=True)
class School:
    name: str
    slug: str
    phase: str = ""
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "School":
        slug = data.get("slug") or to_slug(data["name"])
        return cls(
            name=data["name"],
            slug=slug,
            phase=data.get("phase", ""),
            notes=data.get("notes", ""),
        )


__all__ = ["School"]
