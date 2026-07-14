# Architecture

## Purpose

The Geopolitical Market Forecaster is a small full-stack prototype for turning geopolitical news into market-relevant signals, forecasts, and governance reviews.

## Runtime Flow

```text
News APIs/RSS
    |
NewsIngestionService
    |
SQLite news_items
    |
ForecastPipeline
    |
ScraperAgent -> EconomicAnalystAgent -> PredictorAgent -> GovernorAgent
    |
SQLite insights, forecasts, governance_reviews, audit_events
    |
Sector decision derivation
    |
FastAPI routes + Jinja2 dashboard + WebSocket updates
```

## Agent Design

The project does not use CrewAI, AutoGen, or another agent framework. Each agent is a plain Python class with one clear responsibility:

- `ScraperAgent`: selects stored news or fetches live news when needed.
- `EconomicAnalystAgent`: turns news into market themes and affected markets.
- `PredictorAgent`: creates bounded forecasts from analyst output.
- `GovernorAgent`: reviews forecasts for evidence, confidence, and traceability.

This keeps the system readable for evaluators and easy to test with normal Python unit tests.

## Boundaries

- `config.py`: reads environment settings and resolves the analysis provider.
- `ingestion.py`: handles external news provider clients and normalization.
- `storage.py`: owns SQLite schema and persistence.
- `orchestration/pipeline.py`: coordinates agent hand-offs.
- `main.py`: exposes the FastAPI backend and dashboard routes.
- `realtime.py`: handles WebSocket payloads and optional polling.
- `decisions.py`: derives demonstration sector decisions from stored signal output.

## Maintainability Choices

- The dashboard uses FastAPI/Jinja2 instead of a separate JavaScript frontend to reduce moving parts.
- SQLite keeps local setup simple and transparent.
- External API failures are logged and do not crash the pipeline.
- LLM use is optional; `ANALYSIS_PROVIDER=auto` can use Gemini, OpenAI, optional local Ollama, then deterministic rules.
- Tests cover ingestion, storage, agents, governance, realtime payloads, and dashboard data.
