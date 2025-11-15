"""Utility helpers for lightweight open-web research."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

LOGGER = logging.getLogger(__name__)

USER_AGENT = "EmmaSchoolsResearchBot/0.1 (+https://example.com/emma-schools)"
DEFAULT_HEADERS = {"User-Agent": USER_AGENT}

OFFICIAL_DOMAINS = (
    "gov.uk",
    "ofsted.gov.uk",
    "isi.net",
    "dfe.org.uk",
    "education.gov.uk",
    "schooljotter2.com",
)

NEWS_DOMAINS = (
    "theguardian.com",
    "standard.co.uk",
    "telegraph.co.uk",
    "times.co.uk",
    "news.sky.com",
    "bbc.co.uk",
    "bbc.com",
    "chiswickcalendar.co.uk",
    "richmondandtwickenhamtimes.co.uk",
    "schoolsweek.co.uk",
)

COMMUNITY_DOMAINS = (
    "mumsnet.com",
    "reddit.com",
    "netmums.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
)


@dataclass(slots=True)
class Source:
    title: str
    url: str
    snippet: str
    content: str
    query: str
    reliability: int
    retrieved_at: str


def classify_reliability(url: str) -> int:
    domain = urlparse(url).netloc.lower()
    if any(domain.endswith(suffix) for suffix in OFFICIAL_DOMAINS):
        return 3
    if any(suffix in domain for suffix in NEWS_DOMAINS):
        return 2
    if any(suffix in domain for suffix in COMMUNITY_DOMAINS):
        return 1
    return 2


def fetch_url_text(url: str, *, timeout: int = 12, max_chars: int = 4000) -> str:
    try:
        response = requests.get(url, timeout=timeout, headers=DEFAULT_HEADERS)
        response.raise_for_status()
    except Exception as exc:
        LOGGER.debug("Failed to fetch %s (%s)", url, exc)
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    return text[:max_chars]


def ddg_search(query: str, max_results: int = 4) -> List[dict]:
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


def gather_sources(
    queries: Iterable[str],
    *,
    per_query: int = 3,
    total_limit: int = 12,
    fetch_timeout: int = 12,
    max_chars: int = 4000,
) -> List[Source]:
    seen_urls: set[str] = set()
    collected: List[Source] = []
    for query in queries:
        try:
            results = ddg_search(query, max_results=per_query)
        except Exception as exc:
            LOGGER.warning("Search failed for '%s': %s", query, exc)
            continue
        for result in results:
            url = result.get("href") or result.get("url")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            title = result.get("title") or url
            snippet = result.get("body") or ""
            content = fetch_url_text(url, timeout=fetch_timeout, max_chars=max_chars)
            if not content and not snippet:
                continue
            reliability = classify_reliability(url)
            collected.append(
                Source(
                    title=title.strip(),
                    url=url,
                    snippet=snippet.strip(),
                    content=content.strip() or snippet.strip(),
                    query=query,
                    reliability=reliability,
                    retrieved_at=datetime.now(timezone.utc).date().isoformat(),
                )
            )
            if len(collected) >= total_limit:
                return collected
    return collected


def build_queries(school_name: str, dimension: str, focus: str, max_queries: int) -> List[str]:
    base_terms = re.split(r",|/|;|\\band\\b", focus, flags=re.IGNORECASE)
    queries = []
    seen = set()

    def _add(term: str) -> None:
        cleaned = term.strip()
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            queries.append(f"{school_name} {dimension} {cleaned}")

    for term in base_terms:
        _add(term)

    _add("inspection report")
    _add("results 11+")
    _add("parent reviews")
    _add("notable achievements")
    return queries[:max_queries]


__all__ = ["Source", "gather_sources", "build_queries"]
