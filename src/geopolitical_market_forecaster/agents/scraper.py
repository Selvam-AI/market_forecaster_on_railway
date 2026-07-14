from geopolitical_market_forecaster.config import Settings
from geopolitical_market_forecaster.ingestion import NewsIngestionService
from geopolitical_market_forecaster.models import NewsItem
from geopolitical_market_forecaster.storage import load_recent_news_items


class ScraperAgent:
    """Collects and normalizes market-relevant news."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def collect(self) -> list[NewsItem]:
        stored_items = load_recent_news_items(
            self.settings.database_url,
            self.settings.ingest_page_size,
        )
        if stored_items:
            return stored_items

        _, items, _ = await NewsIngestionService(self.settings).fetch()
        if items:
            return items

        return [
            NewsItem(
                title="Placeholder Middle East market signal",
                source="Local scaffold",
                url="https://example.com/geopolitical-market-signal",
                region=self.settings.default_region,
                summary=(
                    "Placeholder item used until live RSS or news API ingestion "
                    "is implemented."
                ),
            )
        ]
