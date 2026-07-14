# Geopolitical Market Forecaster - Implementation Plan

Last updated: 2026-05-12

## Project Goal

Build an AI-driven dashboard that identifies, explains, and forecasts potential market shifts from global news, beginning with Middle East geopolitical coverage. The system should demonstrate multi-agent orchestration with clear governance, auditability, and human-in-the-loop oversight.

Implementation note: the current agents are plain Python classes coordinated by an explicit pipeline. CrewAI and AutoGen are not used in this project runtime.

## Working Architecture

### 1. Scraper Agent

Purpose: collect validated, current news and market-relevant signals.

Initial responsibilities:
- Fetch live news from selected sources or news APIs.
- Focus first on Middle East geopolitical developments.
- Normalize article metadata: source, URL, title, author if available, published time, region, topic, and raw text or summary.
- Record source and extraction details for auditing.

### 2. Economic Analyst Agent

Purpose: convert raw news into market-relevant interpretation.

Initial responsibilities:
- Summarize each news item.
- Extract economic themes such as energy supply, shipping risk, sanctions, defense spending, currency pressure, inflation, and investor sentiment.
- Classify signal importance: Actionable, FYI, or Noise.
- Identify likely affected sectors, assets, or regions.

### 3. Predictor Agent

Purpose: produce transparent, bounded forecasts from analyst outputs.

Initial responsibilities:
- Forecast possible market shifts with confidence bands.
- Link every forecast to source evidence and analyst reasoning.
- Provide time horizon tags such as intraday, weekly, monthly.
- Avoid unsupported claims by clearly separating evidence, inference, and uncertainty.

### 4. Governor Agent

Purpose: enforce governance, quality control, and auditability.

Initial responsibilities:
- Check source provenance.
- Flag missing citations, weak evidence, duplicated articles, stale data, and overconfident predictions.
- Maintain audit logs for each pipeline run.
- Enforce project rules for transparency and human review.

## Proposed Technical Stack

This stack should be validated as implementation begins.

- Backend: Python with FastAPI for API endpoints and orchestration.
- Agent orchestration: simple explicit Python service classes coordinated by `ForecastPipeline`; CrewAI and AutoGen are not used in the current implementation.
- LLM layer: provider abstraction that can use Gemini, OpenAI, or optional local Ollama, with deterministic rule-based fallback.
- Analysis provider selection: `ANALYSIS_PROVIDER=auto` resolves to Gemini when `GEMINI_API_KEY` is set, OpenAI when `OPENAI_API_KEY` is set, Ollama when `OLLAMA_ENABLED=true`, and rules when no LLM provider is available.
- Data ingestion: RSS feeds and/or zero-cost news APIs first; paid APIs deferred.
- Storage: SQLite for prototype persistence and audit logs.
- Frontend: React/Vite or a lightweight FastAPI-rendered dashboard, depending on project scope chosen next.
- Realtime updates: WebSockets after the basic pipeline is stable.
- Tests: pytest for backend logic and agent governance checks.

## Implementation Phases

### Phase 0 - Repository Setup

Status: Complete

Actions:
- App layout chosen: Python/FastAPI backend scaffold in `project 1/`.
- Added project documentation files.
- Added `.env` and `.env.example` for local API keys and app settings.
- Added dependency and run instructions.
- Added initial test structure.
- Verified source files compile with `python3 -m compileall -q 'project 1/src'`.
- Confirmed local OS prerequisites are installed: `python3.12-venv` and `python3-pip`.
- Created `.venv`, installed dependencies, and installed the local package in editable mode.
- Verified `pytest` passes.
- Verified both `python3 -m geopolitical_market_forecaster.cli run-pipeline` and `gmf run-pipeline` return the placeholder governed forecast.
- Verified SQLite initialization creates `data/geopolitical_market_forecaster.db` with an `audit_events` table.

Deliverable:
- A runnable skeleton with clear setup instructions.

### Phase 1 - First Vertical Slice

Status: Complete

Actions:
- Implemented a small ingest pipeline using Guardian, NewsAPI, and RSS source options.
- Added SQLite persistence for normalized news records.
- Added manual commands to fetch and inspect latest items.
- Added URL-based deduplication.
- Verified Guardian live ingestion with `GUARDIAN_API_KEY`.
- Verified repeated Guardian ingestion deduplicates stored records by URL.
- NewsAPI client is implemented, but live verification returned provider `HTTP 401`; check or regenerate `NEWS_API_KEY` before using it.
- RSS fallback is implemented for no-key ingestion.
- Provider/API failures are sanitized, written to project `ERROR_LOG.txt`, and do not crash ingestion.

Deliverable:
- The project can fetch recent Middle East news and persist normalized records.

### Phase 2 - Agent Pipeline

Status: Complete

Actions:
- Implemented Scraper reading persisted news before falling back to live ingestion.
- Implemented persisted outputs for Economic Analyst, Predictor, and Governor.
- Added audit events for scraper, analyst, predictor, and governor handoffs.
- Added `gmf show-status` to inspect table counts.
- Latest analysis, forecast, and governance rows are refreshed per news URL; audit events preserve run history.
- Added mocked/offline tests for agent pipeline persistence.

Deliverable:
- One command can run news ingestion through analysis, forecast, and governance review.

### Phase 3 - Dashboard

Status: Complete

Actions:
- Built FastAPI/Jinja2 dashboard at `/dashboard`.
- Added dashboard JSON endpoint at `/api/dashboard`.
- Dashboard shows latest news, signal tier, affected markets, forecasts, confidence, approval state, counts, and source links.
- Included source links and operational counts.
- Initial version is server-rendered; richer filters can be added in Phase 4 or a future dashboard enhancement pass.

Deliverable:
- A local dashboard usable for reviewing geopolitical market signals.

### Phase 4 - Realtime Alerts

Status: Complete

Actions:
- Added optional background polling controlled by `ENABLE_BACKGROUND_POLLING`.
- Added WebSocket endpoint at `/ws/alerts`.
- Added manual refresh endpoint at `/api/ingest/run`.
- Added alert severity rules for medium/high dashboard alerts.
- Dashboard now refreshes counts, alerts, and signal rows from WebSocket payloads without a page refresh.

Deliverable:
- New signals can appear in the dashboard without page refresh.

### Phase 5 - Hardening and Governance

Status: Complete

Actions:
- Kept governance basic for this prototype.
- Added `GOVERNANCE_REPORT.md` describing current Governor behavior, limits, and future enhancements.
- Added regression tests for current governance checks.
- Updated README documentation for governance visibility and limitations.
- Documented future active governance work without expanding scope now.

Deliverable:
- A governance-ready prototype with auditable runs and reproducible prompts.

## Immediate Next Actions

1. Review the dashboard and governance report.
2. Decide whether to refine source queries, expand Gemini analysis, or prepare deployment.
3. Optionally add active governance gates in a future enhancement pass.

## Best Next Options

1. Refine source relevance so Guardian/RSS queries return more Middle East market-specific items and fewer unrelated live-blog articles.
2. Expand Gemini analysis once `GEMINI_API_KEY` is available, while keeping `ANALYSIS_PROVIDER=auto` and rule-based fallback as the safe default.
3. Prepare deployment notes and production environment guidance for hosting the FastAPI app, database, runtime logs, and secrets.
4. Improve dashboard usability with filters by source, tier, market, confidence, governance status, and date.
5. Review and commit the deliverable project structure under `project 1/`.
