import asyncio
from contextlib import suppress
from typing import Any

from fastapi import WebSocket

from geopolitical_market_forecaster.config import Settings
from geopolitical_market_forecaster.decisions import build_sector_decisions
from geopolitical_market_forecaster.ingestion import NewsIngestionService
from geopolitical_market_forecaster.orchestration.pipeline import ForecastPipeline
from geopolitical_market_forecaster.storage import (
    dashboard_summary,
    list_dashboard_signals,
    record_audit_event,
    save_news_items,
)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        disconnected: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except RuntimeError:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


def signal_severity(signal: dict[str, Any]) -> str:
    if signal.get("flags"):
        return "high"
    if signal.get("signal_tier") == "Actionable":
        return "high" if signal.get("confidence") in {"Medium", "High"} else "medium"
    if signal.get("approved") is False:
        return "medium"
    return "low"


def dashboard_payload(settings: Settings, event: str) -> dict[str, Any]:
    signals = list_dashboard_signals(settings.database_url)
    alerts = [
        {
            "title": signal["title"],
            "source": signal["source"],
            "url": signal["url"],
            "severity": signal_severity(signal),
            "signal_tier": signal["signal_tier"],
            "confidence": signal["confidence"],
        }
        for signal in signals
        if signal_severity(signal) in {"medium", "high"}
    ]
    return {
        "event": event,
        "summary": dashboard_summary(settings.database_url),
        "signals": signals,
        "alerts": alerts,
        "sector_decisions": build_sector_decisions(signals),
        "analysis_provider": settings.resolved_analysis_provider(),
    }


async def run_ingestion_and_pipeline(settings: Settings, source: str = "auto") -> dict[str, Any]:
    source_used, items, errors = await NewsIngestionService(settings).fetch(source)
    inserted, skipped = save_news_items(settings.database_url, items)
    pipeline_result = await ForecastPipeline(settings).run()
    payload = {
        "source": source_used,
        "fetched": len(items),
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
        "pipeline": {
            "items_collected": pipeline_result.items_collected,
            "insights_created": pipeline_result.insights_created,
            "forecasts_created": pipeline_result.forecasts_created,
            "reviews_created": pipeline_result.reviews_created,
        },
    }
    record_audit_event(settings.database_url, "realtime_refresh", str(payload))
    return payload


async def background_poll(
    settings: Settings,
    manager: ConnectionManager,
    stop_event: asyncio.Event,
) -> None:
    while not stop_event.is_set():
        with suppress(Exception):
            await run_ingestion_and_pipeline(settings)
            await manager.broadcast(dashboard_payload(settings, "background_refresh"))

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=settings.alert_poll_seconds)
        except TimeoutError:
            continue
