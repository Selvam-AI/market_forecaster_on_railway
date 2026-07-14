# Geopolitical Market Forecaster

## Overview

The Geopolitical Market Forecaster is an AI-assisted dashboard that reads real-time Middle East news from live news sources and predicts whether selected Singapore market sectors may benefit or face risk.

The system analyzes geopolitical events related to oil supply, shipping disruption, aviation, and regional instability, then generates simple educational market signals such as `BUY`, `HOLD`, or `AVOID`.

The dashboard currently demonstrates example decision signals for:

- Seatrium (Offshore & Marine exposure)
- Singapore Airlines (Airline exposure)

The application uses a multi-agent pipeline to:

1. Collect and normalize live news articles.
2. Detect market-relevant geopolitical themes.
3. Predict possible sector impact.
4. Display confidence levels, workflow explanations, and supporting evidence links.

This project is designed for learning, evaluation, and demonstration purposes only. It is not financial advice or an automated trading system.

### Problem

- Market watchers, analysts, students, and decision-makers are affected by fast-moving geopolitical news.
- Raw news is noisy, scattered across sources, and difficult to translate into market implications quickly.
- A useful prototype needs ingestion, analysis, forecasting, governance, auditability, and a readable user interface.

### Outcome

- Built a working FastAPI dashboard for geopolitical market signals.
- Added an HTML-rendered sector decision dashboard for example Offshore & Marine and Airline exposure decisions.
- Implemented news ingestion from Guardian, NewsAPI, and RSS source options.
- Added a plain-Python workflow pipeline with four named components: Scraper, Economic Analyst, Predictor, and Governor.
- Persisted news, insights, forecasts, governance reviews, and audit events in SQLite locally and PostgreSQL on Railway.
- Added realtime dashboard refresh via WebSockets.
- Added a governance report and regression tests.
- Current verification: `34 passed`.

---

## Demo

From the project folder, start the backend server:

```bash
scripts/run_dashboard.sh
```

Open the dashboard:

```text
http://127.0.0.1:8000/dashboard
```

Demo walkthrough materials showing how the solution works from the user perspective, covering the main steps from start to finish:

- [Project 1 demo slides (ODP)](docs/project1_demo.odp)
- [Project 1 demo slides (PDF)](docs/project1_demo.pdf)

What the demo is showing:

- News is ingested from configured sources such as Guardian, NewsAPI, or RSS.
- The plain-Python workflow pipeline creates insights, forecasts, governance reviews, and educational sector decisions.
- The dashboard shows two example decision cards, agent workflow, confidence, and evidence links.
- The dashboard can refresh from backend data through the API/WebSocket path.

---

## Technology Stack

### Frontend components

- Jinja2 templates for server-rendered dashboard pages.
- CSS for a quiet operational dashboard layout.
- Browser JavaScript for WebSocket-based realtime updates.

### Backend components

- Python 3.12.
- FastAPI backend application.
- Uvicorn ASGI server.
- SQLite for local persistence and PostgreSQL for Railway persistence.
- psycopg for PostgreSQL connectivity and migration.
- Pydantic models for structured agent data.
- httpx and feedparser for API/RSS ingestion.
- pytest for regression tests.

FastAPI is the backend application framework. Uvicorn is the server process that runs the FastAPI app locally and listens for browser/API requests.

---

## Development Approach with AI

AI tools and services used:

- Codex: project planning, implementation, debugging, refactoring, and documentation.
- Guardian Open Platform: verified live news ingestion.
- NewsAPI: client implemented, but live key verification returned `HTTP 401`.
- LLM analysis provider: `ANALYSIS_PROVIDER=auto` uses Gemini when `GEMINI_API_KEY` is set, otherwise OpenAI when `OPENAI_API_KEY` is set, otherwise Ollama when `OLLAMA_ENABLED=true`, otherwise rule-based analysis.
- Gemini: configured as a placeholder provider.
- OpenAI: configured as the first working LLM analysis provider when Gemini is absent.
- Ollama: optional local fallback if installed, running, and enabled.

The named agents in this application are plain Python classes under `src/geopolitical_market_forecaster/agents/`. CrewAI is not used in the current runtime. They are workflow components with explicit responsibilities, not autonomous external-agent framework workers.

Most pipeline behavior is deterministic and rule-based. The Economic Analyst can optionally call an LLM when `ANALYSIS_PROVIDER` and API keys are configured; if Gemini, OpenAI, or Ollama are unavailable, it falls back to rule-based analysis so the project remains runnable and explainable.

- Scraper Agent: collects and normalizes market-relevant news.
- Economic Analyst Agent: creates market-oriented insights.
- Predictor Agent: creates bounded forecasts from insights.
- Governor Agent: performs basic post-forecast governance checks.

The dashboard also derives educational sector decisions from these outputs:

- Offshore & Marine Exposure: `BUY / HOLD / AVOID` signal for examples such as Seatrium and Marco Polo Marine.
- Airline Exposure: `BUY / HOLD / AVOID` signal for examples such as Singapore Airlines.

These are demonstration signals only, not financial advice. The dashboard intentionally includes an Agent Workflow section so evaluators can see what each plain-Python agent contributes before a `BUY`, `HOLD`, or `AVOID` example appears:

- Scraper Agent: gathers and normalizes source-linked news.
- Economic Analyst Agent: turns news into market-relevant themes.
- Predictor Agent: converts themes into a bounded sector forecast.
- Governor Agent: performs a basic review after prediction and records governance output for auditability.

Key prompts and decisions are recorded in:

[docs/PROMPT_ACTION_LOG.md](docs/PROMPT_ACTION_LOG.md)

Key review points:

- Use FastAPI/Jinja2 first instead of React/Vite to keep the dashboard aligned with the Python backend.
- Keep governance basic for this prototype and document future active governance improvements.
- Default to automatic provider selection with rule-based fallback when LLM keys are absent or unavailable.
- Use automatic analysis provider selection so missing LLM keys fall back safely to rule-based analysis.
- Keep background polling disabled by default to avoid unwanted API usage.

---

## Installation

System prerequisites:

```bash
sudo apt install python3.12-venv python3-pip
```

Project environment:

```bash
cd "project 1"
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Alternative dependency-only install:

```bash
pip install -r requirements.txt
pip install -e .
```

Create or update `.env`:

```bash
cp .env.example .env
```

```text
GEMINI_API_KEY=
OPENAI_API_KEY=
NEWS_API_KEY=your_key_here
GUARDIAN_API_KEY=your_key_here
CURRENTS_API_KEY=
APP_ENV=local
DATABASE_BACKEND=sqlite
DATABASE_URL=sqlite:///data/geopolitical_market_forecaster.db
DATABASE_PUBLIC_URL=
DEFAULT_REGION="Middle East"
DEFAULT_NEWS_QUERY="Middle East geopolitics oil shipping markets"
QUERY_ENERGY='("Brent crude" OR "WTI" OR "energy security") AND (supply OR sanction OR pipeline OR "production cut" OR "OPEC")'
QUERY_SHIPPING='("Red Sea" OR "Bab al-Mandab" OR "Strait of Hormuz" OR "Suez Canal") AND (attack OR shipping OR "freight rates" OR blockade OR reroute)'
QUERY_GEOPOLITICS='("Middle East" OR "regional conflict") AND (escalation OR drone OR missile OR "infrastructure strike" OR "risk premium")'
INGEST_PAGE_SIZE=10
ANALYSIS_PROVIDER=auto
GEMINI_MODEL=gemini-1.5-flash
OPENAI_MODEL=gpt-4o-mini
OLLAMA_ENABLED=false
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1
ERROR_LOG_PATH=ERROR_LOG.txt
ENABLE_BACKGROUND_POLLING=false
ALERT_POLL_SECONDS=300
```

---

## Usage

### Run The Application

You can start the dashboard using the helper script:

```bash
scripts/run_dashboard.sh
```

If you are inside the `scripts/` folder, run:

```bash
./run_dashboard.sh
```
Alternatively:

From the project folder, activate the virtual environment:

```bash
cd "project 1"
source .venv/bin/activate
```

Start the backend server:

```bash
uvicorn geopolitical_market_forecaster.main:app --host 0.0.0.0 --port 8000
```

Open the dashboard in a browser:

```text
http://127.0.0.1:8000/dashboard
```

`source .venv/bin/activate` activates the Python environment for this terminal. `uvicorn` is the local web server that runs the FastAPI backend. `geopolitical_market_forecaster.main:app` points Uvicorn to the app. `--host 0.0.0.0` makes the server reachable inside the VM, and `--port 8000` uses browser port 8000.

Stop the dashboard server by pressing `Ctrl + C` in the terminal where Uvicorn is running.


### Basic Checks

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Static asset check:

```bash
curl -I http://127.0.0.1:8000/static/dashboard.css
```

Dashboard JSON:

```text
http://127.0.0.1:8000/api/dashboard
```

The visible dashboard is centered on two educational company/sector decision cards. It shows a large `BUY`, `HOLD`, or `AVOID` signal, confidence score, agent workflow, and evidence links.

```text
News Event -> Scraper Agent -> Economic Analyst Agent -> Predictor Agent -> Governor Agent -> Sector Decision
```

The raw table counts for news, insights, forecasts, reviews, and audit events remain available through `/api/dashboard`, `gmf show-status`, and the configured database, but they are not shown as top-level dashboard boxes.

Realtime WebSocket:

```text
ws://127.0.0.1:8000/ws/alerts
```

### Railway Deployment

This repository deploys from its root directory. Railway settings:

```text
Build Command: pip install .
Start Command: uvicorn geopolitical_market_forecaster.main:app --host 0.0.0.0 --port $PORT
Healthcheck Path: /health
```

Railway application variables:

```text
APP_ENV=production
DATABASE_BACKEND=postgres
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

Use Railway's private `DATABASE_URL` for the deployed application. `DATABASE_PUBLIC_URL` is intended for migration or local administrative access outside Railway. Do not commit either URL or any API key.

The application creates or upgrades its five PostgreSQL tables during startup. The upgrade repairs the text-only columns created by the original SQLite migration, restores ID sequences and primary keys, and adds URL deduplication for news records. It is safe to run again on later deployments. Create a Railway PostgreSQL backup before the first deployment containing this schema upgrade.

To migrate a local SQLite database from outside Railway:

```bash
python -m geopolitical_market_forecaster.migration \
  --sqlite data/geopolitical_market_forecaster.db \
  --postgres-url "$DATABASE_PUBLIC_URL"
```

### Run The Pipeline

Fetch news:

```bash
gmf ingest-news --source guardian
gmf ingest-news --source newsapi
gmf ingest-news --source rss
gmf ingest-news --source auto
```

Run the agent pipeline:

```bash
gmf run-pipeline
```

Refresh the dashboard manually:

```bash
curl -X POST "http://127.0.0.1:8000/api/ingest/run?source=guardian"
```

View stored news:

```bash
gmf show-news --limit 5
```

View database table counts:

```bash
gmf show-status
```

Provider/API failures do not crash the application. Sanitized failures are appended to `ERROR_LOG.txt`.

`ANALYSIS_PROVIDER=auto` resolves in this order: Gemini if `GEMINI_API_KEY` is present, OpenAI if `OPENAI_API_KEY` is present, Ollama if `OLLAMA_ENABLED=true`, and rule-based analysis if no LLM provider is available. OpenAI/Gemini selection failures can fall back to Ollama when enabled, then to the rule-based analyst so the pipeline can continue.

### Developer Tests

`pytest` runs the automated test suite. Use it to check that ingestion, agents, storage, governance, realtime behavior, and dashboard data still work after code changes.

```bash
pytest
```

The helper script runs the same test command from the project folder:

```bash
scripts/run_tests.sh
```

If you are inside the `scripts/` folder, run:

```bash
./run_tests.sh
```

If a server is running in another terminal and you need to stop it:

```bash
ps -ef | grep uvicorn
kill <PID>
```

---

## Project Structure

```text
project 1/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── src/
├── tests/
├── docs/
├── scripts/
├── data/
└── ERROR_LOG.txt
```

Key folders:

- `src/`: application source code.
- `tests/`: pytest regression tests.
- `docs/`: evaluator guide, architecture notes, implementation plan, prompt log, governance report, tooling notes, and concept documents.
- `scripts/`: small local automation helpers.
- `data/`: local SQLite runtime database; Railway uses PostgreSQL instead.

`scripts/` is useful but intentionally small because most automation is exposed through the `gmf` CLI. `LICENSE` is included because the programme deliverables suggest it; it currently uses a conservative all-rights-reserved notice rather than an open-source license.

---

## Governance

The Governor Agent is currently a basic post-forecast review layer. It checks whether forecasts include evidence, flags high-confidence forecasts for manual review, preserves uncertainty notes, and keeps source URLs attached for traceability.

Governance output is persisted in tables such as `governance_reviews` and `audit_events` in SQLite or PostgreSQL and summarized in `docs/GOVERNANCE_REPORT.md`. It does not yet prevent the Analyst Agent from using weak or unverified source material before analysis. The current dashboard keeps the visible experience focused on the decision signal, agent workflow, and source evidence.

Readable governance report:

```text
docs/GOVERNANCE_REPORT.md
```

Architecture and evaluator notes:

```text
docs/ARCHITECTURE.md
docs/EVALUATOR_GUIDE.md
```

---

## Reflection

What worked:

- Building the backend, agents, database, and dashboard in Python kept the prototype cohesive.
- FastAPI/Jinja2 provided a proper backend and usable dashboard without adding Node tooling.
- Prompt/action logging made the development process traceable.
- Basic governance and audit tables make the workflow explainable.

What failed or needed adjustment:

- NewsAPI returned `HTTP 401`, so Guardian became the verified live ingestion provider.
- Browser access required running Uvicorn outside the Codex sandbox because development is inside a VM.
- The first dashboard route test using FastAPI TestClient hung in the sandbox, so tests were adjusted to validate dashboard data and assets directly.

Changes made:

- Moved the deliverable project structure into `project 1/`.
- Added `docs/`, `scripts/`, and `LICENSE`.
- Kept governance basic for now while documenting future active governance enhancements.

Rationale:

- The project now matches the programme deliverable structure while preserving the working prototype and development record.
