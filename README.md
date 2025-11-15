# Emma Schools Assessment Automation

Automation pipelines for building Emma's long-lived secondary school research vault.  
The project orchestrates Deep Research runs, synthesises evidence, scores schools, and
keeps the MkDocs scoring grid fresh.

## Repository Layout

```
emma-schools-assessment-api-driven/
├── emma_schools/        # Python package with CLI + pipelines
├── raw/                 # Raw Deep Research output (per school)
├── evidence/            # Structured evidence (per school)
├── data/                # Auto-generated CSV exports
├── docs/synthesis/      # MkDocs scoring grid
├── logic/               # Human-readable scoring notes
├── requirements.txt
└── pyproject.toml
```

## Prerequisites

- Python 3.11+
- OpenAI API credentials:
  - `OPENAI_API_KEY` for standard GPT models (synthesis + scoring helpers)
  - `OPENAI_DEEP_RESEARCH_KEY` (falls back to `OPENAI_API_KEY`) for Deep Research
  - Optional: `OPENAI_DEEP_RESEARCH_MODEL` / `OPENAI_DEFAULT_MODEL`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You can install in editable mode if you prefer console scripts:

```bash
pip install -e .
```

## Research Orchestration (Deep Research Stand-in)

- The raw pipeline issues targeted DuckDuckGo queries per school/dimension, pulls the linked pages via `requests`, cleans them with `beautifulsoup4`, and feeds the extracts into GPT for fact extraction.
- Reliability codes are inferred heuristically (official/inspection/government = 3, news/features = 2, forums/community/social = 1) so downstream records can cite the correct score.
- All gathered text flows through the same Fact-ID template, and every fact includes an explicit `Source:` line so the `/raw` files stay machine-parseable.
- Ensure the machine running the CLI has outbound internet access; the scraper respects standard user-agent headers but still depends on reachable public pages.

## Running the CLI

All commands can be invoked via `python -m emma_schools.cli.main ...` or the `emma`
entry point once the project is installed. Use `--verbose` for debug logging.

### Raw Deep Research

```bash
emma raw --school "Kew House School" --dimension academics
emma raw --school "Kew House School" --all-dimensions
emma raw --all                     # all schools & dimensions
```

Each run appends a timestamped block under `/raw/<slug>-raw.md`, refreshes the
source-log section by parsing the fact records, and preserves other sections.

### Evidence Synthesis

```bash
emma evidence --school "Kew House School"
emma evidence --all
```

Uses GPT chat models to summarise raw facts into `/evidence/<slug>.md` according to
the fixed template (no scoring, purely factual bullets).

### Scoring + Grid

```bash
emma score        # writes /data/schools.csv
emma grid         # refreshes docs/synthesis/scoring-grid.md
emma full-run     # raw → evidence → scores → grid
```

Scoring is currently deterministic, keyword-driven, and weighted per
`logic/scoring_rules.md`. The grid generator rewrites only the section between
`<!-- GRID:BEGIN -->` and `<!-- GRID:END -->` while keeping the rest of the doc intact.

## Adding Schools or Dimensions

- Update `emma_schools/config/schools.yml` for new schools.
- Update `emma_schools/config/dimensions.yml` to add/remove dimensions (slugs must
  remain lowercase).
- The CLI consumes these configs automatically; no code changes required.

## Notes

- Raw files follow the `Fact ID / Category / Tags / Fact / Quote / Source / Accessed / Reliability`
  schema. Each run instructs Deep Research to emit this format directly.
- Evidence files never contain scores; they exist purely as distilled references.
- `/data/schools.csv` and `/docs/synthesis/scoring-grid.md` are always
  pipeline-generated—do not edit manually.
- Logging highlights every Deep Research call, synthesis operation, scoring pass, and grid update.
- School slugs use the canonical ASCII + hyphen rule implemented in `emma_schools/core/slugs.py`.
