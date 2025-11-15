"""Command-line interface for the Emma Schools pipelines."""

from __future__ import annotations

import logging
from typing import List, Optional

import typer

from emma_schools.config import School, load_dimensions, load_schools
from emma_schools.core.slugs import to_slug
from emma_schools.pipelines import grid as grid_pipeline
from emma_schools.pipelines import raw_facts, scoring, synthesis

app = typer.Typer(add_completion=False, help="Emma Schools automation CLI.")


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")


def _resolve_school(schools: List[School], identifier: str) -> School:
    slug = to_slug(identifier)
    for school in schools:
        if school.slug == slug or school.name.lower() == identifier.lower():
            return school
    raise typer.BadParameter(f"School not found: {identifier}")


def _normalize_dimensions(dimensions: Optional[List[str]]) -> List[str]:
    if not dimensions:
        return load_dimensions()
    known = set(load_dimensions())
    normalized = [dimension.lower() for dimension in dimensions]
    for dimension in normalized:
        if dimension not in known:
            raise typer.BadParameter(f"Unknown dimension: {dimension}")
    return normalized


@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging.")) -> None:
    _configure_logging(verbose)


@app.command()
def raw(
    school: Optional[str] = typer.Option(None, "--school", help="Target school name or slug."),
    dimension: Optional[str] = typer.Option(None, "--dimension", help="Single dimension to refresh."),
    all_dimensions: bool = typer.Option(
        False,
        "--all-dimensions",
        help="Run for every dimension (default when --dimension is not provided).",
    ),
    all_schools: bool = typer.Option(False, "--all", help="Process every school."),
) -> None:
    """Run Deep Research for raw facts."""

    schools = load_schools()
    dims = _normalize_dimensions([dimension] if dimension else None)
    if all_schools:
        target_dims = dims if not all_dimensions and dimension else load_dimensions()
        raw_facts.run_for_all(schools, target_dims)
        return

    if not school:
        raise typer.BadParameter("Provide --school or use --all.")

    target = _resolve_school(schools, school)
    target_dims = dims if (dimension and not all_dimensions) else load_dimensions()
    raw_facts.run_for_school(target, target_dims)


@app.command()
def evidence(
    school: Optional[str] = typer.Option(None, "--school", help="Target school name or slug."),
    all_schools: bool = typer.Option(False, "--all", help="Process every school."),
    model: Optional[str] = typer.Option(None, "--model", help="Override OpenAI model for synthesis."),
) -> None:
    """Generate structured evidence files from raw facts."""

    schools = load_schools()
    if all_schools:
        synthesis.build_evidence_for_all(schools, model=model)
        return

    if not school:
        raise typer.BadParameter("Provide --school or use --all.")

    target = _resolve_school(schools, school)
    synthesis.build_evidence_for_school(target, model=model)


@app.command()
def score() -> None:
    """Compute scores for all schools and regenerate the CSV."""

    schools = load_schools()
    scoring.score_all(schools)


@app.command()
def grid() -> None:
    """Regenerate the scoring grid Markdown."""

    grid_pipeline.update_scoring_grid()


@app.command("full-run")
def full_run() -> None:
    """Execute the entire pipeline end-to-end."""

    schools = load_schools()
    dimensions = load_dimensions()
    raw_facts.run_for_all(schools, dimensions)
    synthesis.build_evidence_for_all(schools)
    scoring.score_all(schools)
    grid_pipeline.update_scoring_grid()


if __name__ == "__main__":
    app()
