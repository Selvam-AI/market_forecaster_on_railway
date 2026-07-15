# Singapore Equity Geopolitical Forecaster

A Railway-hosted FastAPI dashboard that translates global geopolitical events into understandable implications for Singapore-listed companies.

Production dashboard:

<https://marketforecasteronrailway-production.up.railway.app/dashboard>

> Educational prototype only. The signals are not financial advice. Company-level fundamentals, valuation, debt, earnings, and other risks must be assessed independently.

## Production Architecture

- FastAPI and Uvicorn serve the application.
- Jinja2 renders the dashboard.
- Railway PostgreSQL stores news, insights, forecasts, governance reviews, and audit events.
- Guardian, NewsAPI, and RSS provide configurable news ingestion.
- yfinance searches SGX-listed equities and retrieves market snapshots and finance news from Yahoo Finance without an API key.
- The analysis layer can use OpenAI or fall back to deterministic rules.
- Railway injects configuration through service variables.

This repository is PostgreSQL-only. SQLite, the local database, and the completed SQLite migration utility have been removed.

The two fixed company tabs retain their demonstration price values. The **Search SGX entity** tab retrieves the latest available Yahoo Finance snapshot for a Singapore-listed equity. It accepts a company name, an SGX stock code such as `S58`, or a Yahoo Finance symbol such as `S58.SI`. Non-SGX listings are rejected. Yahoo Finance data may be delayed and is not an exchange-grade live feed.

Search results use the trading currency reported for the selected SGX counter. An SGX listing can therefore display USD or another currency rather than SGD.

The yfinance integration scrapes Yahoo Finance's web endpoints; it is not a contracted Yahoo API integration and does not require an API key or credit card. Results are cached in the application process for five minutes to reduce repeated upstream requests.

## Deploy to Railway

### 1. Create the services

Create one Railway project containing:

1. A service connected to this GitHub repository.
2. A Railway PostgreSQL database service named `Postgres`.

### 2. Configure application variables

Open the Python application service, select **Variables**, and add:

```text
APP_ENV=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

Add the news and model credentials that you intend to use:

```text
OPENAI_API_KEY=
NEWS_API_KEY=
GUARDIAN_API_KEY=
```

Optional settings are documented in `.env.example`. Never commit real credentials.

### 3. Configure deployment

Use the repository root as the Railway root directory.

```text
Build Command: pip install .
Start Command: uvicorn geopolitical_market_forecaster.main:app --host 0.0.0.0 --port $PORT
Healthcheck Path: /health
```

Railway installs the production dependencies declared in `pyproject.toml`. `requirements.txt` contains the same production dependency set for platforms that require it.

### 4. Deploy

Push to the GitHub branch connected to Railway. Railway should build and deploy automatically. If variables are staged, review the staged changes and select **Deploy**.

The application validates `DATABASE_URL` during startup and refuses to start with a missing, SQLite, or otherwise non-PostgreSQL URL.

## Verify the Deployment

Check the health endpoint:

```text
https://YOUR-DOMAIN/health
```

Expected response:

```json
{"status":"ok","environment":"production"}
```

Check the dashboard and static stylesheet:

```text
https://YOUR-DOMAIN/dashboard
https://YOUR-DOMAIN/static/dashboard.css?v=20260715-2
```

The dashboard uses root-relative static paths so CSS and JavaScript remain HTTPS-safe behind Railway's proxy.

## Production Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Railway health check |
| `GET` | `/dashboard` | Rendered dashboard |
| `GET` | `/api/dashboard` | Dashboard JSON snapshot |
| `GET` | `/api/entities/search?q=...` | Search an SGX-listed equity through yfinance |
| `POST` | `/api/ingest/run` | Trigger news ingestion and analysis |
| `POST` | `/pipeline/run` | Run the forecast pipeline |
| `WS` | `/ws/alerts` | Realtime dashboard alerts |

## PostgreSQL Persistence

Railway PostgreSQL persists independently from application deployments. Rebuilding or replacing the application container does not remove database records.

At startup, the application creates any missing tables and performs an idempotent compatibility check for the existing production schema. Back up PostgreSQL before significant schema or storage changes.

Use `${{Postgres.DATABASE_URL}}` from the application service instead of copying a public proxy URL or password into Railway manually.

## Testing Before Deployment

Install the development extras and run the test suite:

```bash
pip install -e ".[dev]"
pytest -q
```

Tests mock PostgreSQL connections; they do not require or modify the Railway production database.

Entity-search tests also mock yfinance, so routine tests do not scrape Yahoo Finance.

## Repository Layout

```text
.
├── src/geopolitical_market_forecaster/
│   ├── agents/
│   ├── orchestration/
│   ├── static/
│   ├── templates/
│   ├── config.py
│   ├── main.py
│   ├── market_data.py
│   └── storage.py
├── tests/
├── .env.example
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Security

- Keep API keys and database URLs in Railway variables.
- Use Railway reference variables for internal service connections.
- Rotate any credential exposed in chat, screenshots, logs, or Git history.
- Redeploy dependent services after rotating PostgreSQL credentials.
- Keep regular Railway PostgreSQL backups.
