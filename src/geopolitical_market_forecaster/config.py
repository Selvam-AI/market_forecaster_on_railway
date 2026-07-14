import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseModel):
    app_env: str = "local"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    news_api_key: str | None = None
    guardian_api_key: str | None = None
    currents_api_key: str | None = None
    database_backend: str = "sqlite"
    database_url: str = "sqlite:///data/geopolitical_market_forecaster.db"
    default_region: str = "Middle East"
    default_news_query: str = "Middle East geopolitics oil shipping markets"
    query_energy: str | None = None
    query_shipping: str | None = None
    query_geopolitics: str | None = None
    ingest_page_size: int = 10
    analysis_provider: str = "auto"
    gemini_model: str = "gemini-1.5-flash"
    openai_model: str = "gpt-4o-mini"
    ollama_enabled: bool = False
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1"
    error_log_path: str = str(ROOT_DIR / "ERROR_LOG.txt")
    enable_background_polling: bool = False
    alert_poll_seconds: int = 300

    def news_queries(self) -> list[str]:
        segmented = [
            self.query_energy,
            self.query_shipping,
            self.query_geopolitics,
        ]
        queries = [query.strip() for query in segmented if query and query.strip()]
        return queries or [self.default_news_query]

    def resolved_analysis_provider(self) -> str:
        provider = self.analysis_provider.lower()
        if provider != "auto":
            return provider
        if self.gemini_api_key:
            return "gemini"
        if self.openai_api_key:
            return "openai"
        if self.ollama_enabled:
            return "ollama"
        return "rule_based"


@lru_cache
def get_settings() -> Settings:
    database_backend = os.getenv("DATABASE_BACKEND", "sqlite").lower()
    if database_backend not in {"sqlite", "postgres"}:
        raise ValueError("DATABASE_BACKEND must be either 'sqlite' or 'postgres'.")

    if database_backend == "postgres":
        database_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PUBLIC_URL")
        if not database_url or not database_url.startswith(("postgresql://", "postgres://")):
            raise ValueError(
                "DATABASE_BACKEND=postgres requires DATABASE_URL or "
                "DATABASE_PUBLIC_URL to contain a PostgreSQL URL."
            )
    else:
        configured_url = os.getenv("DATABASE_URL", "")
        database_url = (
            configured_url
            if configured_url.startswith("sqlite:///")
            else "sqlite:///data/geopolitical_market_forecaster.db"
        )

    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        news_api_key=os.getenv("NEWS_API_KEY") or None,
        guardian_api_key=os.getenv("GUARDIAN_API_KEY") or None,
        currents_api_key=os.getenv("CURRENTS_API_KEY") or None,
        database_backend=database_backend,
        database_url=database_url,
        default_region=os.getenv("DEFAULT_REGION", "Middle East"),
        default_news_query=os.getenv(
            "DEFAULT_NEWS_QUERY",
            "Middle East geopolitics oil shipping markets",
        ),
        query_energy=os.getenv("QUERY_ENERGY") or None,
        query_shipping=os.getenv("QUERY_SHIPPING") or None,
        query_geopolitics=os.getenv("QUERY_GEOPOLITICS") or None,
        ingest_page_size=int(os.getenv("INGEST_PAGE_SIZE", "10")),
        analysis_provider=os.getenv("ANALYSIS_PROVIDER", "auto"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        ollama_enabled=os.getenv("OLLAMA_ENABLED", "false").lower()
        in {"1", "true", "yes", "on"},
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        error_log_path=os.getenv("ERROR_LOG_PATH", str(ROOT_DIR / "ERROR_LOG.txt")),
        enable_background_polling=os.getenv(
            "ENABLE_BACKGROUND_POLLING",
            "false",
        ).lower()
        in {"1", "true", "yes", "on"},
        alert_poll_seconds=int(os.getenv("ALERT_POLL_SECONDS", "300")),
    )
