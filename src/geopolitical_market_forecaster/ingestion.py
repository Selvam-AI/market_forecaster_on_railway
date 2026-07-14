from datetime import datetime
from html import unescape
from typing import Any

import feedparser
import httpx

from geopolitical_market_forecaster.config import Settings
from geopolitical_market_forecaster.error_logging import append_error_log
from geopolitical_market_forecaster.models import NewsItem


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def clean_text(value: str | None) -> str | None:
    if not value:
        return None
    return " ".join(unescape(value).split())


def safe_error_message(source: str, exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        return f"{source} failed: HTTP {status_code} from provider"
    return f"{source} failed: {exc}"


class NewsApiClient:
    base_url = "https://newsapi.org/v2/everything"

    def __init__(self, api_key: str, timeout: float = 15.0):
        self.api_key = api_key
        self.timeout = timeout

    async def fetch(
        self,
        query: str,
        region: str,
        page_size: int,
    ) -> list[NewsItem]:
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": self.api_key,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            payload = response.json()

        if payload.get("status") != "ok":
            message = payload.get("message", "NewsAPI request failed")
            raise RuntimeError(message)

        return [
            self._to_news_item(article, region)
            for article in payload.get("articles", [])
            if article.get("title") and article.get("url")
        ]

    def _to_news_item(self, article: dict[str, Any], region: str) -> NewsItem:
        source = article.get("source") or {}
        return NewsItem(
            title=article["title"],
            source=source.get("name") or "NewsAPI",
            url=article["url"],
            published_at=parse_datetime(article.get("publishedAt")),
            region=region,
            summary=clean_text(article.get("description")),
            raw_text=clean_text(article.get("content")),
        )


class GuardianClient:
    base_url = "https://content.guardianapis.com/search"

    def __init__(self, api_key: str, timeout: float = 15.0):
        self.api_key = api_key
        self.timeout = timeout

    async def fetch(
        self,
        query: str,
        region: str,
        page_size: int,
    ) -> list[NewsItem]:
        params = {
            "q": query,
            "api-key": self.api_key,
            "page-size": page_size,
            "order-by": "newest",
            "show-fields": "trailText,bodyText,byline",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            payload = response.json()

        guardian_response = payload.get("response", {})
        if guardian_response.get("status") != "ok":
            raise RuntimeError("Guardian API request failed")

        return [
            self._to_news_item(result, region)
            for result in guardian_response.get("results", [])
            if result.get("webTitle") and result.get("webUrl")
        ]

    def _to_news_item(self, result: dict[str, Any], region: str) -> NewsItem:
        fields = result.get("fields") or {}
        return NewsItem(
            title=result["webTitle"],
            source="The Guardian",
            url=result["webUrl"],
            published_at=parse_datetime(result.get("webPublicationDate")),
            region=region,
            summary=clean_text(fields.get("trailText")),
            raw_text=clean_text(fields.get("bodyText")),
        )


class RssClient:
    def __init__(self, feed_urls: list[str]):
        self.feed_urls = feed_urls

    async def fetch(self, region: str, page_size: int) -> list[NewsItem]:
        items: list[NewsItem] = []
        for feed_url in self.feed_urls:
            parsed = feedparser.parse(feed_url)
            source = parsed.feed.get("title", feed_url)
            for entry in parsed.entries[:page_size]:
                if not entry.get("title") or not entry.get("link"):
                    continue
                items.append(
                    NewsItem(
                        title=entry["title"],
                        source=source,
                        url=entry["link"],
                        published_at=parse_datetime(entry.get("published")),
                        region=region,
                        summary=clean_text(entry.get("summary")),
                    )
                )
        return items


class NewsIngestionService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def fetch(self, source: str = "auto") -> tuple[str, list[NewsItem], list[str]]:
        errors: list[str] = []
        sources = self._sources_for(source)
        queries = self.settings.news_queries()

        for candidate in sources:
            try:
                if candidate == "guardian":
                    if not self.settings.guardian_api_key:
                        errors.append("Guardian skipped: GUARDIAN_API_KEY is not set.")
                        continue
                    items = await self._fetch_segmented(
                        GuardianClient(self.settings.guardian_api_key),
                        queries,
                    )
                    return candidate, items, errors

                if candidate == "newsapi":
                    if not self.settings.news_api_key:
                        errors.append("NewsAPI skipped: NEWS_API_KEY is not set.")
                        continue
                    items = await self._fetch_segmented(
                        NewsApiClient(self.settings.news_api_key),
                        queries,
                    )
                    return candidate, items, errors

                if candidate == "rss":
                    items = await RssClient(self._rss_feeds()).fetch(
                        self.settings.default_region,
                        self.settings.ingest_page_size,
                    )
                    return candidate, items, errors

            except Exception as exc:
                message = safe_error_message(candidate, exc)
                errors.append(message)
                append_error_log(self.settings.error_log_path, candidate, message)

        return "none", [], errors

    async def _fetch_segmented(
        self,
        client: GuardianClient | NewsApiClient,
        queries: list[str],
    ) -> list[NewsItem]:
        page_size = self.settings.ingest_page_size
        base_size, remainder = divmod(page_size, len(queries))
        collected: list[NewsItem] = []

        for index, query in enumerate(queries):
            query_size = base_size + (1 if index < remainder else 0)
            if query_size == 0:
                continue
            collected.extend(
                await client.fetch(
                    query,
                    self.settings.default_region,
                    query_size,
                )
            )

        unique_items: list[NewsItem] = []
        seen_urls: set[str] = set()
        for item in collected:
            url = str(item.url)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            unique_items.append(item)
        return unique_items[:page_size]

    def _sources_for(self, source: str) -> list[str]:
        if source == "auto":
            return ["guardian", "newsapi", "rss"]
        if source in {"guardian", "newsapi", "rss"}:
            return [source]
        raise ValueError("source must be one of: auto, guardian, newsapi, rss")

    def _rss_feeds(self) -> list[str]:
        return [
            "https://www.aljazeera.com/xml/rss/all.xml",
            "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
        ]
