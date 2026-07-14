import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import psycopg

from geopolitical_market_forecaster.models import (
    EconomicInsight,
    GovernanceReview,
    MarketForecast,
    NewsItem,
)


def database_path(database_url: str) -> Path:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only sqlite database URLs are supported in the prototype.")
    return Path(database_url.removeprefix("sqlite:///"))


def initialize_database(database_url: str) -> None:
    if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
        with psycopg.connect(database_url, sslmode="require") as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_events (
                        id SERIAL PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            connection.commit()
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


def save_news_items(database_url: str, items: Iterable[NewsItem]) -> tuple[int, int]:
    path = database_path(database_url)
    inserted = 0
    skipped = 0

    with sqlite3.connect(path) as connection:
        for item in items:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO news_items (
                    title,
                    source,
                    url,
                    published_at,
                    region,
                    summary,
                    raw_text,
                    collected_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.title,
                    item.source,
                    str(item.url),
                    item.published_at.isoformat() if item.published_at else None,
                    item.region,
                    item.summary,
                    item.raw_text,
                    item.collected_at.isoformat(),
                ),
            )
            if cursor.rowcount:
                inserted += 1
            else:
                skipped += 1

    return inserted, skipped


def record_audit_event(database_url: str, event_type: str, payload: str) -> None:
    with sqlite3.connect(database_path(database_url)) as connection:
        connection.execute(
            """
            INSERT INTO audit_events (event_type, payload, created_at)
            VALUES (?, ?, ?)
            """,
            (event_type, payload, datetime.now(timezone.utc).isoformat()),
        )


def list_recent_news_items(database_url: str, limit: int = 10) -> list[dict[str, str | None]]:
    with sqlite3.connect(database_path(database_url)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT title, source, url, published_at, region, summary, collected_at
            FROM news_items
            ORDER BY COALESCE(published_at, collected_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def load_recent_news_items(database_url: str, limit: int = 10) -> list[NewsItem]:
    with sqlite3.connect(database_path(database_url)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT title, source, url, published_at, region, summary, raw_text, collected_at
            FROM news_items
            ORDER BY COALESCE(published_at, collected_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    items: list[NewsItem] = []
    for row in rows:
        items.append(
            NewsItem(
                title=row["title"],
                source=row["source"],
                url=row["url"],
                published_at=datetime.fromisoformat(row["published_at"])
                if row["published_at"]
                else None,
                region=row["region"],
                summary=row["summary"],
                raw_text=row["raw_text"],
                collected_at=datetime.fromisoformat(row["collected_at"]),
            )
        )
    return items


def save_economic_insight(database_url: str, insight: EconomicInsight) -> None:
    with sqlite3.connect(database_path(database_url)) as connection:
        connection.execute(
            "DELETE FROM economic_insights WHERE news_url = ?",
            (str(insight.news_item.url),),
        )
        connection.execute(
            """
            INSERT INTO economic_insights (
                news_url,
                signal_tier,
                themes,
                affected_markets,
                rationale,
                payload
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(insight.news_item.url),
                insight.signal_tier.value,
                ",".join(insight.themes),
                ",".join(insight.affected_markets),
                insight.rationale,
                insight.model_dump_json(),
            ),
        )


def save_market_forecast(database_url: str, forecast: MarketForecast) -> None:
    with sqlite3.connect(database_path(database_url)) as connection:
        connection.execute(
            "DELETE FROM market_forecasts WHERE news_url = ?",
            (str(forecast.insight.news_item.url),),
        )
        connection.execute(
            """
            INSERT INTO market_forecasts (
                news_url,
                forecast,
                time_horizon,
                confidence,
                evidence,
                uncertainty,
                payload
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(forecast.insight.news_item.url),
                forecast.forecast,
                forecast.time_horizon,
                forecast.confidence.value,
                ",".join(forecast.evidence),
                forecast.uncertainty,
                forecast.model_dump_json(),
            ),
        )


def save_governance_review(database_url: str, review: GovernanceReview) -> None:
    with sqlite3.connect(database_path(database_url)) as connection:
        connection.execute(
            "DELETE FROM governance_reviews WHERE news_url = ?",
            (str(review.forecast.insight.news_item.url),),
        )
        connection.execute(
            """
            INSERT INTO governance_reviews (
                news_url,
                approved,
                flags,
                audit_notes,
                payload
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(review.forecast.insight.news_item.url),
                int(review.approved),
                ",".join(review.flags),
                ",".join(review.audit_notes),
                review.model_dump_json(),
            ),
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

    with sqlite3.connect(database_path(database_url)) as connection:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])


def list_dashboard_signals(database_url: str, limit: int = 25) -> list[dict[str, object]]:
    initialize_database(database_url)
    with sqlite3.connect(database_path(database_url)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
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
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    signals: list[dict[str, object]] = []
    for row in rows:
        signals.append(
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
                "approved": bool(row["approved"]) if row["approved"] is not None else None,
                "flags": split_csv(row["flags"]),
                "audit_notes": split_csv(row["audit_notes"]),
            }
        )
    return signals


def dashboard_summary(database_url: str) -> dict[str, int]:
    return {
        "news_items": count_rows(database_url, "news_items"),
        "economic_insights": count_rows(database_url, "economic_insights"),
        "market_forecasts": count_rows(database_url, "market_forecasts"),
        "governance_reviews": count_rows(database_url, "governance_reviews"),
        "audit_events": count_rows(database_url, "audit_events"),
    }


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]
