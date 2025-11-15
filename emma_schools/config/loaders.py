"""Utilities for loading YAML-based configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import yaml

from emma_schools.config.models import School

CONFIG_DIR = Path(__file__).resolve().parent


def _load_yaml(filename: str) -> dict:
    path = CONFIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_schools() -> List[School]:
    raw = _load_yaml("schools.yml").get("schools", [])
    return [School.from_dict(entry) for entry in raw]


def load_dimensions() -> List[str]:
    return list(_load_yaml("dimensions.yml").get("dimensions", []))


__all__ = ["load_schools", "load_dimensions"]
