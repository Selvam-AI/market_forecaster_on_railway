import os

import pytest

from geopolitical_market_forecaster import config


def test_settings_prefer_internal_postgres_url_when_backend_is_postgres(monkeypatch):
    monkeypatch.setenv("DATABASE_BACKEND", "postgres")
    monkeypatch.setenv("DATABASE_URL", "postgresql://local-user:pass@localhost:5432/local")
    monkeypatch.setenv("DATABASE_PUBLIC_URL", "postgresql://railway-user:pass@tokaido.proxy.rlwy.net:52144/railway?sslmode=require")
    config.get_settings.cache_clear()

    settings = config.get_settings()

    assert settings.database_backend == "postgres"
    assert settings.database_url == "postgresql://local-user:pass@localhost:5432/local"


def test_settings_fall_back_to_public_postgres_url(monkeypatch):
    monkeypatch.setenv("DATABASE_BACKEND", "postgres")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv(
        "DATABASE_PUBLIC_URL",
        "postgresql://railway-user:pass@proxy.example.com:52144/railway?sslmode=require",
    )
    config.get_settings.cache_clear()

    settings = config.get_settings()

    assert settings.database_url.startswith("postgresql://railway-user")


def test_postgres_backend_requires_postgres_url(monkeypatch):
    monkeypatch.setenv("DATABASE_BACKEND", "postgres")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_PUBLIC_URL", raising=False)
    config.get_settings.cache_clear()

    with pytest.raises(ValueError, match="requires DATABASE_URL"):
        config.get_settings()


def test_settings_default_to_sqlite_when_backend_is_sqlite(monkeypatch):
    monkeypatch.setenv("DATABASE_BACKEND", "sqlite")
    monkeypatch.setenv("DATABASE_URL", "postgresql://local-user:pass@localhost:5432/local")
    config.get_settings.cache_clear()

    settings = config.get_settings()

    assert settings.database_backend == "sqlite"
    assert settings.database_url == "sqlite:///data/geopolitical_market_forecaster.db"
