from pathlib import Path

import pytest

from geopolitical_market_forecaster import main
from geopolitical_market_forecaster.config import get_settings
from geopolitical_market_forecaster.main import app


@pytest.mark.asyncio
async def test_dashboard_api_returns_summary_and_signals(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://railway-user:pass@postgres.railway.internal:5432/railway",
    )
    get_settings.cache_clear()
    monkeypatch.setattr(main, "initialize_database", lambda database_url: None)
    monkeypatch.setattr(
        main,
        "dashboard_payload",
        lambda settings, event: {
            "event": event,
            "summary": {"news_items": 1},
            "signals": [{"title": "Oil supply signal"}],
            "sector_decisions": [
                {"category": "Offshore & Marine Exposure"},
                {"category": "Airline Exposure"},
            ],
        },
    )

    try:
        payload = await main.dashboard_data()
    finally:
        get_settings.cache_clear()

    assert payload["summary"]["news_items"] == 1
    assert payload["signals"][0]["title"] == "Oil supply signal"
    assert payload["sector_decisions"][0]["category"] == "Offshore & Marine Exposure"
    assert payload["sector_decisions"][1]["category"] == "Airline Exposure"


def test_dashboard_template_and_styles_exist():
    package_dir = Path(__file__).resolve().parents[1] / "src" / "geopolitical_market_forecaster"
    template_text = (package_dir / "templates" / "dashboard.html").read_text()

    assert 'role="tablist"' in template_text
    assert "Historical Performance & Learning" not in template_text
    assert "System Governance" not in template_text
    assert "Live Global News Feed" in template_text
    assert 'id="tab-search"' in template_text
    assert 'id="entity-search-popover"' in template_text
    assert 'id="entity-search-result"' in template_text
    assert 'class="search-tab-icon"' in template_text
    assert "Singapore Equity Geopolitical Forecaster" in template_text
    assert "Search SGX entity" in template_text
    assert "v2.0" not in template_text
    assert "url_for('static', path='dashboard.css').path" in template_text
    assert "url_for('static', path='dashboard.js').path" in template_text
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
