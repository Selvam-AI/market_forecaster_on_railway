import asyncio

import pytest

from geopolitical_market_forecaster import realtime
from geopolitical_market_forecaster.config import Settings
from geopolitical_market_forecaster.realtime import (
    ConnectionManager,
    dashboard_payload,
    signal_severity,
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


def test_dashboard_payload_includes_alerts(monkeypatch):
    settings = Settings(
        database_url=(
            "postgresql://railway-user:pass@"
            "postgres.railway.internal:5432/railway"
        )
    )
    signals = [
        {
            "title": "Oil shipping risk",
            "source": "Test",
            "url": "https://example.com/realtime",
            "signal_tier": "Actionable",
            "confidence": "Medium",
            "approved": True,
            "flags": [],
            "themes": ["energy", "shipping"],
            "affected_markets": ["offshore", "aviation"],
        }
    ]
    monkeypatch.setattr(realtime, "list_dashboard_signals", lambda database_url: signals)
    monkeypatch.setattr(
        realtime,
        "dashboard_summary",
        lambda database_url: {"news_items": 1},
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
