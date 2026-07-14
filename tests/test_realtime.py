import asyncio

import pytest

from geopolitical_market_forecaster.config import Settings
from geopolitical_market_forecaster.models import NewsItem
from geopolitical_market_forecaster.realtime import (
    ConnectionManager,
    dashboard_payload,
    signal_severity,
)
from geopolitical_market_forecaster.storage import (
    initialize_database,
    save_news_items,
)


def test_signal_severity_uses_tier_confidence_and_flags():
    assert (
        signal_severity(
            {
                "signal_tier": "Actionable",
                "confidence": "Medium",
                "approved": True,
                "flags": [],
            }
        )
        == "high"
    )
    assert (
        signal_severity(
            {
                "signal_tier": "Actionable",
                "confidence": "Low",
                "approved": True,
                "flags": [],
            }
        )
        == "medium"
    )
    assert signal_severity({"flags": ["missing_evidence"]}) == "high"
    assert signal_severity({"signal_tier": "FYI", "approved": True, "flags": []}) == "low"


def test_dashboard_payload_includes_alerts(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'realtime.db'}"
    settings = Settings(database_url=database_url)
    initialize_database(database_url)
    save_news_items(
        database_url,
        [
            NewsItem(
                title="Oil shipping risk",
                source="Test",
                url="https://example.com/realtime",
                summary="Energy and shipping tension.",
            )
        ],
    )

    payload = dashboard_payload(settings, "snapshot")

    assert payload["event"] == "snapshot"
    assert payload["summary"]["news_items"] == 1
    assert payload["signals"][0]["title"] == "Oil shipping risk"
    assert payload["sector_decisions"][0]["decision"] in {"BUY", "HOLD"}
    assert payload["sector_decisions"][1]["decision"] in {"AVOID", "HOLD"}


@pytest.mark.asyncio
async def test_connection_manager_removes_runtime_failures():
    class BrokenSocket:
        async def send_json(self, payload):
            raise RuntimeError("closed")

    manager = ConnectionManager()
    socket = BrokenSocket()
    manager.active_connections.append(socket)

    await manager.broadcast({"event": "test"})

    assert manager.active_connections == []
