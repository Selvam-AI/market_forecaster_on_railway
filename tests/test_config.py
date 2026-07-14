import pytest

from geopolitical_market_forecaster import config


def test_settings_require_railway_postgres_url(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://railway-user:pass@postgres.railway.internal:5432/railway",
    )
    monkeypatch.setenv("APP_ENV", "production")
    config.get_settings.cache_clear()

    settings = config.get_settings()

    assert settings.app_env == "production"
    assert settings.database_url.startswith("postgresql://railway-user")


def test_settings_reject_missing_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    config.get_settings.cache_clear()

    with pytest.raises(ValueError, match="Railway PostgreSQL"):
        config.get_settings()


def test_settings_reject_non_postgres_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///data/legacy.db")
    config.get_settings.cache_clear()

    with pytest.raises(ValueError, match="Railway PostgreSQL"):
        config.get_settings()
