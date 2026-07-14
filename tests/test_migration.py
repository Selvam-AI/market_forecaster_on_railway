import sqlite3
from unittest.mock import MagicMock

import geopolitical_market_forecaster.migration as migration
from geopolitical_market_forecaster.migration import (
    get_sqlite_column_names,
    list_sqlite_tables,
    migrate_sqlite_to_postgres,
)


def test_list_sqlite_tables(tmp_path):
    db_path = tmp_path / "sample.sqlite"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE sample_table (id INTEGER PRIMARY KEY, name TEXT)")
    connection.execute("CREATE TABLE other_table (id INTEGER PRIMARY KEY)")
    connection.commit()
    connection.close()

    tables = list_sqlite_tables(db_path)

    assert tables == ["other_table", "sample_table"]


def test_get_sqlite_column_names(tmp_path):
    db_path = tmp_path / "sample.sqlite"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE sample_table (id INTEGER PRIMARY KEY, name TEXT, active INTEGER)")
    connection.commit()
    connection.close()

    columns = get_sqlite_column_names(db_path, "sample_table")

    assert columns == ["id", "name", "active"]


def test_migration_is_repeat_safe_and_initializes_schema(tmp_path, monkeypatch):
    db_path = tmp_path / "sample.sqlite"
    connection = sqlite3.connect(db_path)
    connection.execute(
        """
        CREATE TABLE news_items (
            id INTEGER PRIMARY KEY,
            title TEXT,
            source TEXT,
            url TEXT,
            published_at TEXT,
            region TEXT,
            summary TEXT,
            raw_text TEXT,
            collected_at TEXT,
            created_at TEXT
        )
        """
    )
    connection.execute(
        """
        INSERT INTO news_items VALUES (
            1, 'Story', 'Example', 'https://example.com/story', NULL,
            'Middle East', 'Summary', NULL, '2026-07-14T12:00:00+00:00',
            '2026-07-14T12:00:00+00:00'
        )
        """
    )
    connection.commit()
    connection.close()

    initialize = MagicMock()
    pg_connection = MagicMock()
    cursor = MagicMock()
    pg_connection.__enter__.return_value = pg_connection
    pg_connection.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.return_value = (None,)
    monkeypatch.setattr(migration, "initialize_database", initialize)
    monkeypatch.setattr(
        migration.psycopg,
        "connect",
        lambda *args, **kwargs: pg_connection,
    )

    migrate_sqlite_to_postgres(
        db_path,
        "postgresql://user:pass@database:5432/app",
    )

    initialize.assert_called_once()
    insert_calls = [
        call for call in cursor.execute.call_args_list if "INSERT INTO" in str(call.args[0])
    ]
    assert len(insert_calls) == 1
    assert "ON CONFLICT DO NOTHING" in str(insert_calls[0].args[0])
