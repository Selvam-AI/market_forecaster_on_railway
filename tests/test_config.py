import os

from geopolitical_market_forecaster import config


def test_settings_use_public_postgres_url_when_backend_is_postgres(monkeypatch):
    monkeypatch.setenv("DATABASE_BACKEND", "postgres")
    monkeypatch.setenv("DATABASE_URL", "postgresql://local-user:pass@localhost:5432/local")
    monkeypatch.setenv("DATABASE_PUBLIC_URL", "postgresql://railway-user:pass@tokaido.proxy.rlwy.net:52144/railway?sslmode=require")
    config.get_settings.cache_clear()

    settings = config.get_settings()

    assert settings.database_backend == "postgres"
    assert settings.database_url == "postgresql://railway-user:pass@tokaido.proxy.rlwy.net:52144/railway?sslmode=require"


def test_settings_default_to_sqlite_when_backend_is_sqlite(monkeypatch):
    monkeypatch.setenv("DATABASE_BACKEND", "sqlite")
    monkeypatch.setenv("DATABASE_URL", "postgresql://local-user:pass@localhost:5432/local")
    config.get_settings.cache_clear()

    settings = config.get_settings()

    assert settings.database_backend == "sqlite"
    assert settings.database_url == "sqlite:///data/geopolitical_market_forecaster.db"
