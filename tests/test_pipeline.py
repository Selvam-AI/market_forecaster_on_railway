import pytest

from geopolitical_market_forecaster.config import Settings
from geopolitical_market_forecaster.models import NewsItem
from geopolitical_market_forecaster.orchestration.pipeline import ForecastPipeline
from geopolitical_market_forecaster.storage import (
    count_rows,
    initialize_database,
    save_news_items,
)


@pytest.mark.asyncio
async def test_pipeline_returns_governed_result(monkeypatch, tmp_path):
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

    settings = Settings(database_url=f"sqlite:///{tmp_path / 'pipeline.db'}")
    result = await ForecastPipeline(settings).run()

    assert result.items_collected == 1
    assert result.insights_created == 1
    assert result.forecasts_created == 1
    assert result.reviews_created == 1
    assert len(result.reviews) == 1
    assert result.reviews[0].approved is True


@pytest.mark.asyncio
async def test_pipeline_uses_stored_news_and_persists_agent_outputs(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'pipeline.db'}"
    settings = Settings(database_url=database_url)
    initialize_database(database_url)
    save_news_items(
        database_url,
        [
            NewsItem(
                title="Oil shipping tension rises",
                source="Stored",
                url="https://example.com/stored-pipeline",
                summary="Energy and shipping risk in the region.",
            )
        ],
    )

    result = await ForecastPipeline(settings).run()

    assert result.items_collected == 1
    assert count_rows(database_url, "economic_insights") == 1
    assert count_rows(database_url, "market_forecasts") == 1
    assert count_rows(database_url, "governance_reviews") == 1
    assert count_rows(database_url, "audit_events") == 4
