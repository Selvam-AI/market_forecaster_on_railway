# Evaluator Guide

## What To Review First

1. Start with `README.md` for the problem, setup, usage, and reflection.
2. Open the dashboard at `http://127.0.0.1:8000/dashboard`.
3. Review `docs/ARCHITECTURE.md` for the system flow.
4. Review `docs/GOVERNANCE_REPORT.md` for what the Governor Agent checks today.
5. Review `docs/PROMPT_ACTION_LOG.md` for the AI-assisted development record.

## What The Project Demonstrates

- A working backend server using FastAPI.
- A browser dashboard for non-technical review.
- An HTML-rendered sector decision dashboard with Offshore & Marine and Airline examples.
- News ingestion from API/RSS sources.
- A plain-Python agent pipeline with clear responsibilities.
- SQLite persistence for news, insights, forecasts, governance reviews, and audit logs.
- Basic governance checks with persisted governance output.
- Regression tests for the important workflow pieces.

## How The Project Stays Explainable

- Agents are normal Python classes, not hidden framework magic.
- Forecasts keep source URLs and evidence attached.
- Sector decisions show the reasoning chain from news event to agent workflow to sector decision.
- The Agent Workflow section is included so evaluators can see what the Scraper, Economic Analyst, Predictor, and Governor contribute before a `BUY`, `HOLD`, or `AVOID` example appears.
- Governance output is visible in the database and summarized in `docs/GOVERNANCE_REPORT.md`.
- LLM analysis is optional and falls back through OpenAI/Ollama/rules depending on local configuration.
- Prompt/action history and implementation decisions are documented.

## How To Verify Quickly

```bash
cd "project 1"
source .venv/bin/activate
pytest
scripts/run_dashboard.sh
```

Then open:

```text
http://127.0.0.1:8000/dashboard
```

## Current Limitations

- Governance is a review layer, not a strict pre-analysis blocker.
- Forecasts and dashboard decisions are learning/demo signals only and should not be treated as financial advice.
- News source quality scoring and dashboard filters are future improvements.
- Deployment hardening is documented as a next step, not completed production hosting.
