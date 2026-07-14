import argparse
import os
import sqlite3
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def list_sqlite_tables(db_path: str | os.PathLike[str]) -> list[str]:
    connection = sqlite3.connect(str(db_path))
    try:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    finally:
        connection.close()
    return [row[0] for row in rows]


def get_sqlite_column_names(db_path: str | os.PathLike[str], table_name: str) -> list[str]:
    connection = sqlite3.connect(str(db_path))
    try:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    finally:
        connection.close()
    return [row[1] for row in rows]


def migrate_sqlite_to_postgres(sqlite_path: str | os.PathLike[str], postgres_url: str) -> None:
    sqlite_db = Path(sqlite_path)
    if not sqlite_db.exists():
        raise FileNotFoundError(f"SQLite database not found: {sqlite_db}")

    with sqlite3.connect(sqlite_db) as sqlite_conn:
        sqlite_conn.row_factory = sqlite3.Row
        tables = list_sqlite_tables(sqlite_db)

        with psycopg.connect(postgres_url, sslmode="require") as pg_conn:
            with pg_conn.cursor() as cursor:
                for table_name in tables:
                    rows = sqlite_conn.execute(f"SELECT * FROM {table_name}").fetchall()
                    if not rows:
                        continue

                    columns = get_sqlite_column_names(sqlite_db, table_name)
                    placeholders = ", ".join(["%s"] * len(columns))
                    column_sql = ", ".join(columns)

                    cursor.execute(
                        f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join([f'{col} TEXT' for col in columns])})"
                    )

                    for row in rows:
                        values = [row[col] for col in columns]
                        cursor.execute(
                            f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholders})",
                            values,
                        )

            pg_conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate a local SQLite database into PostgreSQL")
    parser.add_argument("--sqlite", default="data/geopolitical_market_forecaster.db", help="Path to the SQLite database")
    parser.add_argument("--postgres-url", default=os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL"), help="PostgreSQL connection URL")
    args = parser.parse_args()

    if not args.postgres_url:
        raise SystemExit("Please provide --postgres-url or set DATABASE_PUBLIC_URL/DATABASE_URL")

    migrate_sqlite_to_postgres(args.sqlite, args.postgres_url)
    print(f"Migration complete from {args.sqlite} to PostgreSQL")


if __name__ == "__main__":
    main()
