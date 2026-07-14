from geopolitical_market_forecaster.models import (
    Confidence,
    EconomicInsight,
    MarketForecast,
)


class PredictorAgent:
    """Produces bounded forecasts from economic insights."""

    async def forecast(self, insight: EconomicInsight) -> MarketForecast:
        return MarketForecast(
            insight=insight,
            forecast="Monitor for short-term volatility in exposed sectors.",
            time_horizon="weekly",
            confidence=Confidence.low,
            evidence=[str(insight.news_item.url)],
            uncertainty="Placeholder forecast; live data and LLM reasoning not yet connected.",
        )
