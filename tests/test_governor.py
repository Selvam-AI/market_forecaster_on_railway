import pytest

from geopolitical_market_forecaster.agents.governor import GovernorAgent
from geopolitical_market_forecaster.models import (
    Confidence,
    EconomicInsight,
    MarketForecast,
    NewsItem,
    SignalTier,
)


def make_forecast(confidence: Confidence, evidence: list[str]) -> MarketForecast:
    item = NewsItem(
        title="Governance test",
        source="Test",
        url="https://example.com/governance",
    )
    insight = EconomicInsight(
        news_item=item,
        signal_tier=SignalTier.fyi,
        themes=["market sentiment"],
        affected_markets=["regional equities"],
        rationale="Test insight",
    )
    return MarketForecast(
        insight=insight,
        forecast="Test forecast",
        time_horizon="weekly",
        confidence=confidence,
        evidence=evidence,
        uncertainty="Test uncertainty",
    )


@pytest.mark.asyncio
async def test_governor_approves_low_confidence_forecast_with_evidence():
    review = await GovernorAgent().review(
        make_forecast(Confidence.low, ["https://example.com/governance"])
    )

    assert review.approved is True
    assert review.flags == []


@pytest.mark.asyncio
async def test_governor_flags_missing_evidence():
    review = await GovernorAgent().review(make_forecast(Confidence.low, []))

    assert review.approved is False
    assert "missing_evidence" in review.flags


@pytest.mark.asyncio
async def test_governor_flags_high_confidence_for_manual_review():
    review = await GovernorAgent().review(
        make_forecast(Confidence.high, ["https://example.com/governance"])
    )

    assert review.approved is False
    assert "high_confidence_requires_manual_review" in review.flags
