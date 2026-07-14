from unittest.mock import MagicMock

from geopolitical_market_forecaster.models import NewsItem
from geopolitical_market_forecaster.storage import (
    count_rows,
    initialize_database,
    list_recent_news_items,
    load_recent_news_items,
    save_news_items,
)


def test_save_news_items_deduplicates_by_url(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    initialize_database(database_url)

    item = NewsItem(
        title="Shipping risk rises",
        source="Example",
        url="https://example.com/story",
        summary="Summary",
    )

    inserted, skipped = save_news_items(database_url, [item, item])
    rows = list_recent_news_items(database_url)

    assert inserted == 1
    assert skipped == 1
    assert len(rows) == 1
    assert rows[0]["title"] == "Shipping risk rises"
    assert count_rows(database_url, "news_items") == 1


def test_load_recent_news_items_returns_models(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    initialize_database(database_url)
    save_news_items(
        database_url,
        [
            NewsItem(
                title="Stored item",
                source="Example",
                url="https://example.com/stored",
                summary="Stored summary",
            )
        ],
    )

    items = load_recent_news_items(database_url)

    assert len(items) == 1
    assert items[0].title == "Stored item"


def test_postgres_news_insert_uses_conflict_deduplication(monkeypatch):
    connection = MagicMock()
    cursor = MagicMock()
    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.side_effect = [(1,), None]
    monkeypatch.setattr(
        "geopolitical_market_forecaster.storage.psycopg.connect",
        lambda *args, **kwargs: connection,
    )
    item = NewsItem(
        title="Postgres story",
        source="Example",
        url="https://example.com/postgres-story",
    )

    inserted, skipped = save_news_items(
        "postgresql://user:pass@database:5432/app",
        [item, item],
    )

    assert (inserted, skipped) == (1, 1)
    assert "ON CONFLICT (url) DO NOTHING" in cursor.execute.call_args_list[0].args[0]


def test_postgres_recent_news_returns_dictionary_rows(monkeypatch):
    connection = MagicMock()
    cursor = MagicMock()
    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchall.return_value = [
        {
            "title": "Stored in Postgres",
            "source": "Example",
            "url": "https://example.com/postgres-read",
            "published_at": None,
            "region": "Middle East",
            "summary": "Summary",
            "collected_at": "2026-07-14T12:00:00+00:00",
        }
    ]
    monkeypatch.setattr(
        "geopolitical_market_forecaster.storage.psycopg.connect",
        lambda *args, **kwargs: connection,
    )

    rows = list_recent_news_items(
        "postgresql://user:pass@database:5432/app",
        limit=5,
    )

    assert rows[0]["title"] == "Stored in Postgres"
    assert cursor.execute.call_args.args[1] == (5,)


def test_postgres_count_rows_uses_supported_table(monkeypatch):
    connection = MagicMock()
    cursor = MagicMock()
    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.return_value = (7,)
    monkeypatch.setattr(
        "geopolitical_market_forecaster.storage.psycopg.connect",
        lambda *args, **kwargs: connection,
    )

    result = count_rows(
        "postgresql://user:pass@database:5432/app",
        "news_items",
    )

    assert result == 7
    assert cursor.execute.call_args.args[0] == "SELECT COUNT(*) FROM news_items"


def test_postgres_initialization_repairs_migrated_text_schema(monkeypatch):
    connection = MagicMock()
    cursor = MagicMock()
    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor
    monkeypatch.setattr(
        "geopolitical_market_forecaster.storage.psycopg.connect",
        lambda *args, **kwargs: connection,
    )

    initialize_database("postgresql://user:pass@database:5432/app")

    executed_sql = "\n".join(str(call.args[0]) for call in cursor.execute.call_args_list)
    assert "ALTER COLUMN id TYPE BIGINT" in executed_sql
    assert "ALTER COLUMN created_at TYPE TIMESTAMPTZ" in executed_sql
    assert "news_items_url_unique_idx" in executed_sql
