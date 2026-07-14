import sqlite3

from geopolitical_market_forecaster.migration import (
    get_sqlite_column_names,
    list_sqlite_tables,
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
