import httpx
import pytest

from geopolitical_market_forecaster.config import Settings
from geopolitical_market_forecaster.ingestion import (
    GuardianClient,
    NewsApiClient,
    NewsIngestionService,
)


@pytest.mark.asyncio
async def test_newsapi_client_maps_articles(monkeypatch):
    async def handler(request):
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "articles": [
                    {
                        "source": {"name": "Example Source"},
                        "title": "Oil markets watch shipping risk",
                        "description": "A short description.",
                        "url": "https://example.com/newsapi-story",
                        "publishedAt": "2026-05-12T01:02:03Z",
                        "content": "Article content",
                    }
                ],
            },
        )

    async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: async_client(
            transport=httpx.MockTransport(handler),
            timeout=kwargs.get("timeout"),
        ),
    )

    items = await NewsApiClient("test-key").fetch("Middle East", "Middle East", 5)

    assert len(items) == 1
    assert items[0].source == "Example Source"
    assert str(items[0].url) == "https://example.com/newsapi-story"


@pytest.mark.asyncio
async def test_guardian_client_maps_results(monkeypatch):
    async def handler(request):
        return httpx.Response(
            200,
            json={
                "response": {
                    "status": "ok",
                    "results": [
                        {
                            "webTitle": "Middle East tensions affect markets",
                            "webUrl": "https://www.theguardian.com/world/example",
                            "webPublicationDate": "2026-05-12T04:05:06Z",
                            "fields": {
                                "trailText": "Summary text",
                                "bodyText": "Body text",
                            },
                        }
                    ],
                }
            },
        )

    async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: async_client(
            transport=httpx.MockTransport(handler),
            timeout=kwargs.get("timeout"),
        ),
    )

    items = await GuardianClient("test-key").fetch("Middle East", "Middle East", 5)

    assert len(items) == 1
    assert items[0].source == "The Guardian"
    assert items[0].summary == "Summary text"


@pytest.mark.asyncio
async def test_ingestion_logs_provider_error_and_continues(monkeypatch, tmp_path):
    async def guardian_fetch_stub(self, query, region, page_size):
        request = httpx.Request("GET", "https://content.guardianapis.com/search")
        response = httpx.Response(500, request=request)
        raise httpx.HTTPStatusError("boom", request=request, response=response)

    async def newsapi_fetch_stub(self, query, region, page_size):
        from geopolitical_market_forecaster.models import NewsItem

        return [
            NewsItem(
                title="NewsAPI recovery item",
                source="NewsAPI",
                url="https://example.com/newsapi-recovery",
            )
        ]

    async def rss_fetch_stub(self, region, page_size):
        from geopolitical_market_forecaster.models import NewsItem

        return [
            NewsItem(
                title="RSS fallback item",
                source="RSS",
                url="https://example.com/rss-fallback",
            )
        ]

    monkeypatch.setattr(GuardianClient, "fetch", guardian_fetch_stub)
    monkeypatch.setattr(NewsApiClient, "fetch", newsapi_fetch_stub)
    monkeypatch.setattr(
        "geopolitical_market_forecaster.ingestion.RssClient.fetch",
        rss_fetch_stub,
    )

    error_log_path = tmp_path / "ERROR_LOG.txt"
    settings = Settings(
        guardian_api_key="guardian-key",
        news_api_key="news-key",
        error_log_path=str(error_log_path),
    )

    source, items, errors = await NewsIngestionService(settings).fetch("auto")

    assert source == "newsapi"
    assert len(items) == 1
    assert items[0].title == "NewsAPI recovery item"
    assert errors == ["guardian failed: HTTP 500 from provider"]
    assert "guardian failed: HTTP 500 from provider" in error_log_path.read_text()


@pytest.mark.asyncio
async def test_segmented_queries_share_page_size_and_deduplicate(monkeypatch):
    calls = []

    async def guardian_fetch_stub(self, query, region, page_size):
        from geopolitical_market_forecaster.models import NewsItem

        calls.append((query, page_size))
        return [
            NewsItem(
                title=f"Story for {query}",
                source="The Guardian",
                url=f"https://example.com/{len(calls)}",
            )
        ]

    monkeypatch.setattr(GuardianClient, "fetch", guardian_fetch_stub)
    settings = Settings(
        guardian_api_key="guardian-key",
        ingest_page_size=10,
        query_energy="energy query",
        query_shipping="shipping query",
        query_geopolitics="geopolitics query",
    )

    source, items, errors = await NewsIngestionService(settings).fetch("guardian")

    assert source == "guardian"
    assert errors == []
    assert calls == [
        ("energy query", 4),
        ("shipping query", 3),
        ("geopolitics query", 3),
    ]
    assert len(items) == 3
