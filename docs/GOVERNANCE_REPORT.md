# Governance Report

Last updated: 2026-05-12

## Current Governance Position

The project currently uses a basic Governor Agent implemented as a plain Python class. CrewAI is not used. The Governor is a post-forecast review layer, not a strict preventive gate.

The Governor Agent reviews each forecast after the Predictor Agent creates it. Its output is persisted to the SQLite `governance_reviews` table and summarized in this report. The current dashboard keeps the visible experience focused on the educational decision signal, agent workflow, and evidence links.

## What The Governor Enforces Today

- Forecasts must include evidence.
- High-confidence forecasts are flagged for manual review.
- Forecasts must keep uncertainty visible.
- Source URLs must remain attached for traceability.

## What The Governor Produces

Each governance review includes:

- `approved`: whether the forecast passed current checks.
- `flags`: issues requiring attention.
- `audit_notes`: short notes explaining the review basis.

## Where To Inspect Governance Output

Dashboard:

```text
http://127.0.0.1:8000/dashboard
```

The dashboard shows where the Governor fits in the Agent Workflow. Detailed governance review rows are available through SQLite and this report rather than as a separate dashboard column.

CLI:

```bash
cd "project 1"
source .venv/bin/activate
gmf run-pipeline
gmf show-status
```

SQLite tables:

- `governance_reviews`
- `audit_events`
- `market_forecasts`
- `economic_insights`

Database path:

```text
project 1/data/geopolitical_market_forecaster.db
```

## What Governance Does Not Yet Do

The Governor does not yet block the Analyst Agent from using weak, stale, or unverified source material before analysis. It also does not yet apply source allowlists, robots/API compliance enforcement, source quality scores, or minimum evidence thresholds before prediction.

## Future Governance Enhancements

Future versions can make governance more active and more visible by adding:

- Pre-analysis source quality gates.
- Pre-forecast evidence checks.
- Source allowlists and compliance notes.
- Stale article rejection.
- More detailed dashboard governance explanations if the dashboard later needs active governance visibility.
- Prompt and model version tracking for LLM-based analysis.
