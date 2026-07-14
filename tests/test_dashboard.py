from pathlib import Path

import pytest

from geopolitical_market_forecaster.config import get_settings
from geopolitical_market_forecaster.main import app, dashboard_data
from geopolitical_market_forecaster.models import NewsItem
from geopolitical_market_forecaster.storage import (
    initialize_database,
    save_news_items,
)


@pytest.mark.asyncio
async def test_dashboard_api_returns_summary_and_signals(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'dashboard.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    initialize_database(database_url)
    save_news_items(
        database_url,
        [
            NewsItem(
                title="Oil supply signal",
                source="Test",
                url="https://example.com/dashboard-signal",
                summary="Energy and shipping signal.",
            )
        ],
    )

    try:
        payload = await dashboard_data()
    finally:
        get_settings.cache_clear()

    assert payload["summary"]["news_items"] == 1
    assert payload["signals"][0]["title"] == "Oil supply signal"
    assert payload["sector_decisions"][0]["category"] == "Offshore & Marine Exposure"
    assert payload["sector_decisions"][1]["category"] == "Airline Exposure"


def test_dashboard_template_and_styles_exist():
    package_dir = Path(__file__).resolve().parents[1] / "src" / "geopolitical_market_forecaster"

    assert 'role="tablist"' in (
        package_dir / "templates" / "dashboard.html"
    ).read_text()
    assert "Historical Performance & Learning" not in (
        package_dir / "templates" / "dashboard.html"
    ).read_text()
    assert "System Governance" not in (
        package_dir / "templates" / "dashboard.html"
    ).read_text()
    assert "Live Global News Feed" in (
        package_dir / "templates" / "dashboard.html"
    ).read_text()
    assert ".entity-tabs" in (package_dir / "static" / "dashboard.css").read_text()
    assert ".wind-badge" in (
        package_dir / "static" / "dashboard.css"
    ).read_text()
    assert ".score-track" in (package_dir / "static" / "dashboard.css").read_text()


def test_static_asset_mount_resolves_css_and_javascript():
    static_route = next(route for route in app.routes if route.name == "static")

    css_path, css_stat = static_route.app.lookup_path("dashboard.css")
    js_path, js_stat = static_route.app.lookup_path("dashboard.js")

    assert static_route.path == "/static"
    assert Path(css_path).name == "dashboard.css"
    assert css_stat is not None
    assert Path(js_path).name == "dashboard.js"
    assert js_stat is not None
