from __future__ import annotations

from datetime import datetime, timezone
from time import monotonic
from typing import Any
from urllib.parse import quote

import yfinance as yf


SEARCH_CACHE_SECONDS = 300
SEARCH_CACHE_LIMIT = 128
_SEARCH_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


class EntityNotFoundError(LookupError):
    pass


class MarketDataUnavailableError(RuntimeError):
    pass


def search_market_entity(query: str) -> dict[str, Any]:
    normalized_query = " ".join(query.split())
    if len(normalized_query) < 2:
        raise EntityNotFoundError("Enter at least two characters.")

    cache_key = normalized_query.casefold()
    cached = _SEARCH_CACHE.get(cache_key)
    if cached and monotonic() - cached[0] < SEARCH_CACHE_SECONDS:
        return cached[1]

    try:
        search = yf.Search(
            normalized_query,
            max_results=8,
            news_count=8,
            lists_count=0,
            include_cb=False,
            enable_fuzzy_query=True,
            timeout=12,
            raise_errors=True,
        )
        entity = _select_equity(normalized_query, search.quotes)
        if entity is None:
            raise EntityNotFoundError(
                f'No publicly listed company was found for "{normalized_query}".'
            )

        result = _build_market_snapshot(normalized_query, entity, search.news)
    except EntityNotFoundError:
        raise
    except Exception as error:
        raise MarketDataUnavailableError(
            "Yahoo Finance data is temporarily unavailable. Please try again shortly."
        ) from error

    if len(_SEARCH_CACHE) >= SEARCH_CACHE_LIMIT:
        oldest_key = min(_SEARCH_CACHE, key=lambda key: _SEARCH_CACHE[key][0])
        _SEARCH_CACHE.pop(oldest_key, None)
    _SEARCH_CACHE[cache_key] = (monotonic(), result)
    return result


def _select_equity(query: str, quotes: list[dict[str, Any]]) -> dict[str, Any] | None:
    equities = [
        item
        for item in quotes
        if item.get("symbol") and str(item.get("quoteType", "")).upper() == "EQUITY"
    ]
    if not equities:
        return None

    query_key = query.casefold()

    def rank(item: dict[str, Any]) -> tuple[int, int]:
        symbol = str(item.get("symbol", "")).casefold()
        names = [
            str(item.get(key, "")).casefold()
            for key in ("longname", "shortname", "name")
        ]
        if symbol == query_key:
            return (0, 0)
        if query_key in names:
            return (1, 0)
        if any(name.startswith(query_key) for name in names if name):
            return (2, len(symbol))
        return (3, len(symbol))

    return min(equities, key=rank)


def _build_market_snapshot(
    query: str,
    entity: dict[str, Any],
    news_items: list[dict[str, Any]],
) -> dict[str, Any]:
    symbol = str(entity["symbol"]).upper()
    company_name = (
        entity.get("longname")
        or entity.get("shortname")
        or entity.get("name")
        or symbol
    )
    exchange = entity.get("exchDisp") or entity.get("exchange") or "Unknown exchange"
    currency = entity.get("currency")
    market_price = _number(entity.get("regularMarketPrice"))
    previous_close = _number(entity.get("regularMarketPreviousClose"))
    change_percent = _number(entity.get("regularMarketChangePercent"))

    if market_price is None or previous_close is None or not currency:
        ticker = yf.Ticker(symbol)
        market_price, previous_close, currency = _ticker_values(
            ticker,
            market_price,
            previous_close,
            currency,
        )

    if change_percent is None and market_price is not None and previous_close:
        change_percent = ((market_price - previous_close) / previous_close) * 100

    return {
        "query": query,
        "symbol": symbol,
        "company_name": str(company_name),
        "exchange": str(exchange),
        "quote_type": "Equity",
        "currency": str(currency or ""),
        "market_price": _format_price(market_price, currency),
        "day_change": _format_change(change_percent),
        "change_direction": _change_direction(change_percent),
        "price_available": market_price is not None,
        "source": "Yahoo Finance via yfinance",
        "source_url": f"https://finance.yahoo.com/quote/{quote(symbol, safe='')}",
        "news": _normalize_news(news_items)[:6],
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "Market data may be delayed. This search does not generate a geopolitical "
            "wind direction or investment recommendation."
        ),
    }


def _ticker_values(
    ticker: Any,
    market_price: float | None,
    previous_close: float | None,
    currency: str | None,
) -> tuple[float | None, float | None, str | None]:
    try:
        fast_info = ticker.fast_info
        market_price = market_price or _number(fast_info.get("last_price"))
        previous_close = previous_close or _number(fast_info.get("previous_close"))
        currency = currency or fast_info.get("currency")
    except Exception:
        pass

    if market_price is not None and previous_close is not None:
        return market_price, previous_close, currency

    try:
        history = ticker.history(period="5d", interval="1d", auto_adjust=False)
        closes = history["Close"].dropna().tolist()
        if closes:
            market_price = market_price or _number(closes[-1])
        if len(closes) > 1:
            previous_close = previous_close or _number(closes[-2])
    except Exception:
        pass
    return market_price, previous_close, currency


def _normalize_news(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in items:
        content = item.get("content") if isinstance(item.get("content"), dict) else item
        provider = content.get("provider")
        canonical_url = content.get("canonicalUrl")
        title = content.get("title")
        source = (
            provider.get("displayName")
            if isinstance(provider, dict)
            else content.get("publisher")
        )
        url = (
            canonical_url.get("url")
            if isinstance(canonical_url, dict)
            else content.get("link") or content.get("url")
        )
        published_at = content.get("pubDate") or _timestamp_to_iso(
            content.get("providerPublishTime")
        )
        if title and url:
            normalized.append(
                {
                    "title": str(title),
                    "source": str(source or "Yahoo Finance"),
                    "url": str(url),
                    "published_at": str(published_at or ""),
                }
            )
    return normalized


def _number(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("raw")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _format_price(value: float | None, currency: str | None) -> str:
    if value is None:
        return "Unavailable"
    prefixes = {"SGD": "S$", "USD": "US$", "EUR": "€", "GBP": "£", "JPY": "¥"}
    prefix = prefixes.get(str(currency or "").upper(), f"{currency} " if currency else "")
    return f"{prefix}{value:,.2f}"


def _format_change(value: float | None) -> str:
    return "Unavailable" if value is None else f"{value:+.2f}%"


def _change_direction(value: float | None) -> str:
    if value is None or value == 0:
        return "neutral"
    return "positive" if value > 0 else "negative"


def _timestamp_to_iso(value: Any) -> str:
    timestamp = _number(value)
    if timestamp is None:
        return ""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def clear_entity_search_cache() -> None:
    _SEARCH_CACHE.clear()
