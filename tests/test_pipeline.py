from unittest.mock import MagicMock

import pytest

from geopolitical_market_forecaster.config import Settings
from geopolitical_market_forecaster.models import NewsItem
from geopolitical_market_forecaster.orchestration import pipeline
from geopolitical_market_forecaster.orchestration.pipeline import ForecastPipeline


@pytest.mark.asyncio
async def test_pipeline_returns_and_persists_governed_result(monkeypatch):
    async def collect_stub(self):
        return [
            NewsItem(
                title="Pipeline test item",
                source="Test",
                url="https://example.com/pipeline-test",
                summary="Test summary",
            )
        ]

    monkeypatch.setattr(
        "geopolitical_market_forecaster.agents.scraper.ScraperAgent.collect",
        collect_stub,
    )
    storage_calls = {
        name: MagicMock()
        for name in (
            "initialize_database",
            "record_audit_event",
            "save_economic_insight",
            "save_market_forecast",
            "save_governance_review",
        )
    }
    for name, mock in storage_calls.items():
        monkeypatch.setattr(pipeline, name, mock)

    settings = Settings(
        database_url=(
            "postgresql://railway-user:pass@"
            "postgres.railway.internal:5432/railway"
        )
    )
    result = await ForecastPipeline(settings).run()

    assert result.items_collected == 1
    assert result.insights_created == 1
    assert result.forecasts_created == 1
    assert result.reviews_created == 1
    assert result.reviews[0].approved is True
    storage_calls["initialize_database"].assert_called_once()
    storage_calls["save_economic_insight"].assert_called_once()
    storage_calls["save_market_forecast"].assert_called_once()
    storage_calls["save_governance_review"].assert_called_once()
    assert storage_calls["record_audit_event"].call_count == 4
