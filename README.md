# SGX Geopolitical Forecaster

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

## Migration and Railway Deployment Notes

### Why SQLite was replaced with PostgreSQL

The first version stored application data in a local SQLite file. That was convenient during development, but it was not suitable for this Railway deployment:

- A Railway application container can be rebuilt or replaced during a deployment, so a database file stored inside that container is not durable production storage.
- SQLite is a single local file and is not designed to be shared safely by multiple application instances.
- Keeping a production database file on an application volume would add volume mounting, backup, and single-instance constraints.
- Railway PostgreSQL runs as an independent database service, survives application redeployments, supports concurrent connections, and has a normal backup path.

The local SQLite records were migrated once into the Railway PostgreSQL service. After the data was verified, the SQLite runtime path, local `data/` directory, and one-time migration utility were removed. The application now deliberately rejects a missing or SQLite `DATABASE_URL` instead of silently creating a new local database.

### Migration challenges and resolutions

SQLite and PostgreSQL do not use identical schemas or SQL syntax. The migration required more than copying the database file:

- SQLite-style auto-incrementing identifiers were replaced with PostgreSQL sequences and primary keys.
- Parameterized queries use psycopg's `%s` placeholders rather than SQLite `?` placeholders.
- Duplicate news URLs are handled with PostgreSQL `ON CONFLICT` behavior.
- Imported identifier and timestamp fields required normalization. The startup compatibility check converts legacy text identifiers to numeric IDs, attaches sequences, restores primary-key and `NOT NULL` constraints, converts `created_at` to `TIMESTAMPTZ`, and advances each sequence beyond the highest imported ID.
- Table and index creation is idempotent, so a new deployment can safely check the existing schema without deleting production data.

This startup compatibility logic is in `storage.py`. It is intended to keep the migrated production schema usable; it is not a replacement for backups before future structural migrations.

### Why the deployed dashboard initially had no CSS

The stylesheet existed in the Railway image and opening `/static/dashboard.css` directly returned the file. The browser still rendered an unstyled dashboard because the generated asset link used `http://` while the public Railway page used `https://`. Modern browsers block that insecure stylesheet as mixed content.

Two production-safe changes resolved the issue:

1. `main.py` derives absolute template and static directories from `Path(__file__).resolve().parent`. Asset discovery therefore does not depend on Railway starting Uvicorn from `/app` or any other working directory.
2. `dashboard.html` uses FastAPI/Jinja's named static route and takes its root-relative `.path`, producing `/static/dashboard.css` and `/static/dashboard.js`. The browser keeps the public page's HTTPS scheme instead of receiving an incorrect HTTP asset URL.

Version query strings are added to static asset links so browsers fetch updated CSS and JavaScript after deployment. Linux filename matching is case-sensitive, so the template references must also match the committed filenames exactly.

### Why separate frontend and backend services are unnecessary

This project is a server-rendered monolithic web application. FastAPI handles API and WebSocket routes, Jinja2 renders the HTML, and the same FastAPI process serves the CSS and JavaScript from the package's `static/` directory. Railway therefore needs one application service and one separate PostgreSQL service—not separate frontend and backend application services.

The `templates/` and `static/` directories are still distinct inside the Python package for organization and packaging, but both are deployed in the same Python build. A separate frontend service would become useful only if the interface were changed to an independently built single-page application, such as React or Vue, with its own release lifecycle or hosting requirements.

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

Railway variables must be configured on the **Python application service**, not only on the PostgreSQL service or in the local `.env` file. The local `.env` file is ignored by Git and is not uploaded to Railway.

Use the reference variable exactly as shown:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

This lets Railway inject the PostgreSQL service's current private connection URL. It is safer and easier to maintain than copying a public proxy URL and password. If the database service has a different name, update `Postgres` in the reference to match it.

After adding or editing variables, apply any staged changes and redeploy the application service. Confirm that the variables are in the same Railway environment as the deployment, such as `production`. Changing a local `.env`, changing a variable in another Railway environment, or editing only the database service will not update the running Python container.

If PostgreSQL credentials are regenerated, the reference variable resolves to the new value after the application is redeployed. Any manually copied connection URL must instead be replaced by hand. API keys or database credentials exposed in a screenshot, terminal output, chat, or Git history should be rotated immediately.

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

Railway's `RAILWAY_GIT_COMMIT_SHA` identifies the commit used for the running deployment. Compare it with `git rev-parse HEAD` and the latest commit on the connected GitHub branch when diagnosing an apparently stale deployment. Creating a local commit is not enough: it must be pushed to the exact repository and branch connected to the Railway application service.

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
https://YOUR-DOMAIN/static/dashboard.css?v=20260715-3
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
