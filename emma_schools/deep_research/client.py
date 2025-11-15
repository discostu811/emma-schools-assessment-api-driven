"""Wrappers around OpenAI APIs plus custom research orchestration."""

from __future__ import annotations

import logging
import os
from typing import List

from openai import OpenAI

from emma_schools.deep_research.search import build_queries, gather_sources
from emma_schools.deep_research.prompts import DIMENSION_FOCUS

LOGGER = logging.getLogger(__name__)


def _get_api_key(env_var: str, fallback: str | None = None) -> str:
    key = os.getenv(env_var)
    if key:
        return key
    if fallback:
        key = os.getenv(fallback)
    if not key:
        raise EnvironmentError(
            f"Missing API key. Set {env_var} or {fallback or 'OPENAI_API_KEY'}."
        )
    return key


def _client_for_key(env_var: str, fallback: str | None = None) -> OpenAI:
    api_key = _get_api_key(env_var, fallback)
    return OpenAI(api_key=api_key)


def _format_sources_for_prompt(sources) -> str:
    blocks = []
    for idx, source in enumerate(sources, start=1):
        extract = source.content[:1800]
        block = [
            f"[Source {idx}] reliability={source.reliability} accessed={source.retrieved_at}",
            f"Title: {source.title}",
            f"URL: {source.url}",
            f"Query: {source.query}",
        ]
        if source.snippet:
            block.append(f"Snippet: {source.snippet}")
        block.append(f"Extract:\n{extract}")
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def run_deep_research(
    topic: str,
    instruction: str,
    *,
    max_queries: int = 10,
    timeout: int = 600,
    school_name: str | None = None,
    dimension: str | None = None,
) -> str:
    """Perform a multi-step open-web research pass using GPT orchestration."""

    school = school_name or topic
    dimension_key = (dimension or "").lower()
    focus = DIMENSION_FOCUS.get(dimension_key, "")
    queries = build_queries(school, dimension_key or "overview", focus, max_queries)
    if not queries:
        queries = [f"{school} {dimension_key} facts"]
    sources = gather_sources(
        queries,
        per_query=2,
        total_limit=max(6, max_queries),
    )
    LOGGER.info(
        "Research run | school=%s | dimension=%s | queries=%s | sources=%s",
        school,
        dimension_key or "general",
        len(queries),
        len(sources),
    )
    if not sources:
        LOGGER.warning("No sources found for %s (%s); running instruction only.", school, dimension_key)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an autonomous research analyst. Return only the requested "
                    "Markdown structure, citing verifiable sources you know."
                ),
            },
            {"role": "user", "content": instruction},
        ]
        return run_chat_completion(messages, model=os.getenv("OPENAI_DEEP_RESEARCH_MODEL"), timeout=timeout)

    source_block = _format_sources_for_prompt(sources)
    reliability_hint = (
        "Reliability codes: 3=official/inspection/government, 2=news or vetted publications, "
        "1=community/forum/social."
    )
    guardrails = (
        "Use ONLY the provided sources. When you cite, reference their Source number and include "
        'a line like "- Source: <title> (<url>) — Accessed: <date> — Reliability: <code>". '
        "Do not invent sources or facts."
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a meticulous research analyst tasked with emitting structured raw fact records. "
                "Follow the templates precisely and ground every statement in the supplied sources."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{instruction}\n\n{guardrails}\n{reliability_hint}\n\n"
                f"SOURCES:\n{source_block}"
            ),
        },
    ]
    model = os.getenv("OPENAI_DEEP_RESEARCH_MODEL", "gpt-4.1-mini")
    return run_chat_completion(messages, model=model, timeout=timeout)


def run_chat_completion(
    messages: List[dict],
    *,
    model: str | None = None,
    timeout: int | None = None,
) -> str:
    """Call the standard GPT chat endpoint using the Responses API."""

    client = _client_for_key("OPENAI_API_KEY")
    resolved_model = model or os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
    LOGGER.debug("Chat completion | model=%s | messages=%s", resolved_model, len(messages))
    kwargs = {"model": resolved_model, "input": messages}
    if timeout:
        kwargs["timeout"] = timeout
    response = client.responses.create(**kwargs)
    return response.output_text


__all__ = ["run_deep_research", "run_chat_completion"]
