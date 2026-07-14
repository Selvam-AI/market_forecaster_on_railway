import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import psycopg
from psycopg.rows import dict_row

from geopolitical_market_forecaster.models import (
    EconomicInsight,
    GovernanceReview,
    MarketForecast,
    NewsItem,
)


POSTGRES_PREFIXES = ("postgresql://", "postgres://")
POSTGRES_TABLES = (
    "audit_events",
    "news_items",
    "economic_insights",
    "market_forecasts",
    "governance_reviews",
)
_INITIALIZED_DATABASE_URLS: set[str] = set()


def is_postgres(database_url: str) -> bool:
    return database_url.startswith(POSTGRES_PREFIXES)


def database_path(database_url: str) -> Path:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Expected a sqlite:/// or postgresql:// database URL.")
    return Path(database_url.removeprefix("sqlite:///"))


def initialize_database(database_url: str) -> None:
    if database_url in _INITIALIZED_DATABASE_URLS:
        return

    if is_postgres(database_url):
        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_events (
                        id SERIAL PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS news_items (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        source TEXT NOT NULL,
                        url TEXT NOT NULL UNIQUE,
                        published_at TEXT,
                        region TEXT NOT NULL,
                        summary TEXT,
                        raw_text TEXT,
                        collected_at TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS economic_insights (
                        id SERIAL PRIMARY KEY,
                        news_url TEXT NOT NULL,
                        signal_tier TEXT NOT NULL,
                        themes TEXT NOT NULL,
                        affected_markets TEXT NOT NULL,
                        rationale TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS market_forecasts (
                        id SERIAL PRIMARY KEY,
                        news_url TEXT NOT NULL,
                        forecast TEXT NOT NULL,
                        time_horizon TEXT NOT NULL,
                        confidence TEXT NOT NULL,
                        evidence TEXT NOT NULL,
                        uncertainty TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS governance_reviews (
                        id SERIAL PRIMARY KEY,
                        news_url TEXT NOT NULL,
                        approved INTEGER NOT NULL,
                        flags TEXT NOT NULL,
                        audit_notes TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                _upgrade_postgres_schema(cursor)
        _INITIALIZED_DATABASE_URLS.add(database_url)
        return

    path = database_path(database_url)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS news_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                published_at TEXT,
                region TEXT NOT NULL,
                summary TEXT,
                raw_text TEXT,
                collected_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS economic_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_url TEXT NOT NULL,
                signal_tier TEXT NOT NULL,
                themes TEXT NOT NULL,
                affected_markets TEXT NOT NULL,
                rationale TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS market_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_url TEXT NOT NULL,
                forecast TEXT NOT NULL,
                time_horizon TEXT NOT NULL,
                confidence TEXT NOT NULL,
                evidence TEXT NOT NULL,
                uncertainty TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS governance_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_url TEXT NOT NULL,
                approved INTEGER NOT NULL,
                flags TEXT NOT NULL,
                audit_notes TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    _INITIALIZED_DATABASE_URLS.add(database_url)


def _upgrade_postgres_schema(cursor: psycopg.Cursor) -> None:
    """Repair tables created by the original SQLite-to-Postgres text migration."""
    for table_name in POSTGRES_TABLES:
        sequence_name = f"{table_name}_id_seq"
        primary_key_name = f"{table_name}_pkey"

        cursor.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = '{table_name}'
                      AND column_name = 'id'
                      AND data_type = 'text'
                ) THEN
                    ALTER TABLE {table_name}
                    ALTER COLUMN id TYPE BIGINT USING id::BIGINT;
                END IF;
            END $$
            """
        )
        cursor.execute(f"CREATE SEQUENCE IF NOT EXISTS {sequence_name}")
        cursor.execute(
            f"ALTER SEQUENCE {sequence_name} OWNED BY {table_name}.id"
        )
        cursor.execute(
            f"ALTER TABLE {table_name} ALTER COLUMN id "
            f"SET DEFAULT nextval('{sequence_name}')"
        )
        cursor.execute(f"ALTER TABLE {table_name} ALTER COLUMN id SET NOT NULL")
        cursor.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conrelid = '{table_name}'::regclass
                      AND contype = 'p'
                ) THEN
                    ALTER TABLE {table_name}
                    ADD CONSTRAINT {primary_key_name} PRIMARY KEY (id);
                END IF;
            END $$
            """
        )
        cursor.execute(
            f"SELECT setval('{sequence_name}', COALESCE(MAX(id), 1), "
            f"MAX(id) IS NOT NULL) FROM {table_name}"
        )
        cursor.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = '{table_name}'
                      AND column_name = 'created_at'
                      AND data_type = 'text'
                ) THEN
                    UPDATE {table_name}
                    SET created_at = NULL
                    WHERE created_at IS NOT NULL AND BTRIM(created_at) = '';

                    ALTER TABLE {table_name}
                    ALTER COLUMN created_at TYPE TIMESTAMPTZ
                    USING created_at::TIMESTAMPTZ;
                END IF;
            END $$
            """
        )
        cursor.execute(
            f"UPDATE {table_name} SET created_at = CURRENT_TIMESTAMP "
            "WHERE created_at IS NULL"
        )
        cursor.execute(
            f"ALTER TABLE {table_name} ALTER COLUMN created_at "
            "SET DEFAULT CURRENT_TIMESTAMP"
        )
        cursor.execute(
            f"ALTER TABLE {table_name} ALTER COLUMN created_at SET NOT NULL"
        )

    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS news_items_url_unique_idx "
        "ON news_items (url)"
    )


def save_news_items(database_url: str, items: Iterable[NewsItem]) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    if is_postgres(database_url):
        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                for item in items:
                    cursor.execute(
                        """
                        INSERT INTO news_items (
                            title, source, url, published_at, region,
                            summary, raw_text, collected_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                        RETURNING id
                        """,
                        _news_item_values(item),
                    )
                    if cursor.fetchone():
                        inserted += 1
                    else:
                        skipped += 1
        return inserted, skipped

    with sqlite3.connect(database_path(database_url)) as connection:
        for item in items:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO news_items (
                    title, source, url, published_at, region,
                    summary, raw_text, collected_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _news_item_values(item),
            )
            if cursor.rowcount:
                inserted += 1
            else:
                skipped += 1
    return inserted, skipped


def _news_item_values(item: NewsItem) -> tuple[object, ...]:
    return (
        item.title,
        item.source,
        str(item.url),
        item.published_at.isoformat() if item.published_at else None,
        item.region,
        item.summary,
        item.raw_text,
        item.collected_at.isoformat(),
    )


def record_audit_event(database_url: str, event_type: str, payload: str) -> None:
    created_at = datetime.now(timezone.utc)
    if is_postgres(database_url):
        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO audit_events (event_type, payload, created_at)
                    VALUES (%s, %s, %s)
                    """,
                    (event_type, payload, created_at),
                )
        return

    with sqlite3.connect(database_path(database_url)) as connection:
        connection.execute(
            """
            INSERT INTO audit_events (event_type, payload, created_at)
            VALUES (?, ?, ?)
            """,
            (event_type, payload, created_at.isoformat()),
        )


def list_recent_news_items(database_url: str, limit: int = 10) -> list[dict[str, object]]:
    query = """
        SELECT title, source, url, published_at, region, summary, collected_at
        FROM news_items
        ORDER BY COALESCE(published_at, collected_at) DESC
        LIMIT {placeholder}
    """
    rows = _fetch_rows(database_url, query, (limit,))
    return [dict(row) for row in rows]


def load_recent_news_items(database_url: str, limit: int = 10) -> list[NewsItem]:
    query = """
        SELECT title, source, url, published_at, region, summary, raw_text, collected_at
        FROM news_items
        ORDER BY COALESCE(published_at, collected_at) DESC
        LIMIT {placeholder}
    """
    rows = _fetch_rows(database_url, query, (limit,))
    return [
        NewsItem(
            title=row["title"],
            source=row["source"],
            url=row["url"],
            published_at=_as_datetime(row["published_at"]),
            region=row["region"],
            summary=row["summary"],
            raw_text=row["raw_text"],
            collected_at=_as_datetime(row["collected_at"])
            or datetime.now(timezone.utc),
        )
        for row in rows
    ]


def save_economic_insight(database_url: str, insight: EconomicInsight) -> None:
    values = (
        str(insight.news_item.url),
        insight.signal_tier.value,
        ",".join(insight.themes),
        ",".join(insight.affected_markets),
        insight.rationale,
        insight.model_dump_json(),
    )
    _replace_by_news_url(
        database_url,
        "economic_insights",
        "signal_tier, themes, affected_markets, rationale, payload",
        values,
    )


def save_market_forecast(database_url: str, forecast: MarketForecast) -> None:
    values = (
        str(forecast.insight.news_item.url),
        forecast.forecast,
        forecast.time_horizon,
        forecast.confidence.value,
        ",".join(forecast.evidence),
        forecast.uncertainty,
        forecast.model_dump_json(),
    )
    _replace_by_news_url(
        database_url,
        "market_forecasts",
        "forecast, time_horizon, confidence, evidence, uncertainty, payload",
        values,
    )


def save_governance_review(database_url: str, review: GovernanceReview) -> None:
    values = (
        str(review.forecast.insight.news_item.url),
        int(review.approved),
        ",".join(review.flags),
        ",".join(review.audit_notes),
        review.model_dump_json(),
    )
    _replace_by_news_url(
        database_url,
        "governance_reviews",
        "approved, flags, audit_notes, payload",
        values,
    )


def _replace_by_news_url(
    database_url: str,
    table_name: str,
    column_sql: str,
    values: tuple[object, ...],
) -> None:
    columns = [column.strip() for column in column_sql.split(",")]
    all_columns = ["news_url", *columns]

    if is_postgres(database_url):
        placeholders = ", ".join(["%s"] * len(values))
        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"DELETE FROM {table_name} WHERE news_url = %s",
                    (values[0],),
                )
                cursor.execute(
                    f"INSERT INTO {table_name} ({', '.join(all_columns)}) "
                    f"VALUES ({placeholders})",
                    values,
                )
        return

    placeholders = ", ".join(["?"] * len(values))
    with sqlite3.connect(database_path(database_url)) as connection:
        connection.execute(
            f"DELETE FROM {table_name} WHERE news_url = ?",
            (values[0],),
        )
        connection.execute(
            f"INSERT INTO {table_name} ({', '.join(all_columns)}) "
            f"VALUES ({placeholders})",
            values,
        )


def count_rows(database_url: str, table_name: str) -> int:
    allowed_tables = {
        "news_items",
        "economic_insights",
        "market_forecasts",
        "governance_reviews",
        "audit_events",
    }
    if table_name not in allowed_tables:
        raise ValueError(f"Unsupported table: {table_name}")

    if is_postgres(database_url):
        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row = cursor.fetchone()
    else:
        with sqlite3.connect(database_path(database_url)) as connection:
            row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return int(row[0])


def list_dashboard_signals(database_url: str, limit: int = 25) -> list[dict[str, object]]:
    initialize_database(database_url)
    query = """
        SELECT
            n.title,
            n.source,
            n.url,
            n.published_at,
            n.region,
            n.summary,
            i.signal_tier,
            i.themes,
            i.affected_markets,
            i.rationale,
            f.forecast,
            f.time_horizon,
            f.confidence,
            f.uncertainty,
            g.approved,
            g.flags,
            g.audit_notes
        FROM news_items n
        LEFT JOIN economic_insights i ON i.news_url = n.url
        LEFT JOIN market_forecasts f ON f.news_url = n.url
        LEFT JOIN governance_reviews g ON g.news_url = n.url
        ORDER BY COALESCE(n.published_at, n.collected_at) DESC
        LIMIT {placeholder}
    """
    rows = _fetch_rows(database_url, query, (limit,))

    return [
        {
            "title": row["title"],
            "source": row["source"],
            "url": row["url"],
            "published_at": row["published_at"],
            "region": row["region"],
            "summary": row["summary"],
            "signal_tier": row["signal_tier"] or "Pending",
            "themes": split_csv(row["themes"]),
            "affected_markets": split_csv(row["affected_markets"]),
            "rationale": row["rationale"],
            "forecast": row["forecast"] or "Pending pipeline run",
            "time_horizon": row["time_horizon"] or "Pending",
            "confidence": row["confidence"] or "Pending",
            "uncertainty": row["uncertainty"],
            "approved": bool(row["approved"])
            if row["approved"] is not None
            else None,
            "flags": split_csv(row["flags"]),
            "audit_notes": split_csv(row["audit_notes"]),
        }
        for row in rows
    ]


def _fetch_rows(
    database_url: str,
    query: str,
    params: tuple[object, ...],
) -> list[dict[str, object] | sqlite3.Row]:
    if is_postgres(database_url):
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query.format(placeholder="%s"), params)
                return list(cursor.fetchall())

    with sqlite3.connect(database_path(database_url)) as connection:
        connection.row_factory = sqlite3.Row
        return list(connection.execute(query.format(placeholder="?"), params).fetchall())


def _as_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def dashboard_summary(database_url: str) -> dict[str, int]:
    return {
        "news_items": count_rows(database_url, "news_items"),
        "economic_insights": count_rows(database_url, "economic_insights"),
        "market_forecasts": count_rows(database_url, "market_forecasts"),
        "governance_reviews": count_rows(database_url, "governance_reviews"),
        "audit_events": count_rows(database_url, "audit_events"),
    }


def split_csv(value: object) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]
