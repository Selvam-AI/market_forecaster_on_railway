from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from geopolitical_market_forecaster import main, market_data
from geopolitical_market_forecaster.market_data import (
    EntityNotFoundError,
    MarketDataUnavailableError,
    clear_entity_search_cache,
    search_market_entity,
)


@pytest.fixture(autouse=True)
def clear_search_cache():
    clear_entity_search_cache()
    yield
    clear_entity_search_cache()


def test_entity_search_returns_market_snapshot_and_news(monkeypatch):
    fake_search = SimpleNamespace(
        quotes=[
            {
                "symbol": "D05.SI",
                "quoteType": "EQUITY",
                "longname": "DBS Group Holdings Ltd",
                "exchDisp": "Singapore",
                "currency": "SGD",
                "regularMarketPrice": 45.2,
                "regularMarketPreviousClose": 44.75,
            }
        ],
        news=[
            {
                "content": {
                    "title": "DBS announces a market update",
                    "provider": {"displayName": "Example News"},
                    "canonicalUrl": {"url": "https://example.com/dbs"},
                    "pubDate": "2026-07-15T01:00:00Z",
                }
            }
        ],
    )
    search_mock = MagicMock(return_value=fake_search)
    monkeypatch.setattr(market_data.yf, "Search", search_mock)

    result = search_market_entity("DBS Group")

    assert result["symbol"] == "D05.SI"
    assert result["company_name"] == "DBS Group Holdings Ltd"
    assert result["market_price"] == "S$45.20"
    assert result["day_change"] == "+1.01%"
    assert result["quote_type"] == "SGX equity"
    assert result["news"][0]["source"] == "Example News"
    assert result["source"] == "Yahoo Finance via yfinance"


def test_entity_search_prefers_exact_ticker_and_caches(monkeypatch):
    fake_search = SimpleNamespace(
        quotes=[
            {
                "symbol": "DBSDY",
                "quoteType": "EQUITY",
                "shortname": "DBS ADR",
                "currency": "USD",
                "regularMarketPrice": 100,
                "regularMarketPreviousClose": 100,
            },
            {
                "symbol": "D05.SI",
                "quoteType": "EQUITY",
                "shortname": "DBS Group",
                "currency": "SGD",
                "regularMarketPrice": 45,
                "regularMarketPreviousClose": 44,
            },
        ],
        news=[],
    )
    search_mock = MagicMock(return_value=fake_search)
    monkeypatch.setattr(market_data.yf, "Search", search_mock)

    first = search_market_entity("D05")
    second = search_market_entity("  d05  ")

    assert first["symbol"] == "D05.SI"
    assert second == first
    search_mock.assert_called_once()


def test_entity_search_rejects_non_sgx_equity(monkeypatch):
    monkeypatch.setattr(
        market_data.yf,
        "Search",
        lambda *args, **kwargs: SimpleNamespace(
            quotes=[{"symbol": "AAPL", "quoteType": "EQUITY"}],
            news=[],
        ),
    )

    with pytest.raises(EntityNotFoundError, match="No SGX-listed equity"):
        search_market_entity("Apple")


def test_entity_search_hides_provider_failure(monkeypatch):
    def failed_search(*args, **kwargs):
        raise RuntimeError("provider internals")

    monkeypatch.setattr(market_data.yf, "Search", failed_search)

    with pytest.raises(MarketDataUnavailableError, match="temporarily unavailable"):
        search_market_entity("DBS")


def test_entity_search_endpoint_maps_not_found_to_404(monkeypatch):
    def not_found(query):
        raise EntityNotFoundError("No SGX-listed equity found.")

    monkeypatch.setattr(main, "search_market_entity", not_found)

    with pytest.raises(HTTPException) as error:
        main.entity_search("missing company")

    assert error.value.status_code == 404
    assert error.value.detail == "No SGX-listed equity found."


def test_entity_search_endpoint_maps_provider_failure_to_502(monkeypatch):
    def unavailable(query):
        raise MarketDataUnavailableError("Provider temporarily unavailable.")

    monkeypatch.setattr(main, "search_market_entity", unavailable)

    with pytest.raises(HTTPException) as error:
        main.entity_search("DBS")

    assert error.value.status_code == 502
