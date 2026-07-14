import pytest

from geopolitical_market_forecaster.agents.analyst import EconomicAnalystAgent
from geopolitical_market_forecaster.config import Settings
from geopolitical_market_forecaster.models import NewsItem, SignalTier


@pytest.mark.asyncio
async def test_rule_based_analysis_detects_market_themes():
    item = NewsItem(
        title="Oil shipping risk rises near the Red Sea",
        source="Test",
        url="https://example.com/oil-shipping",
        summary="Regional tension affects energy and shipping markets.",
    )

    insight = await EconomicAnalystAgent(
        Settings(analysis_provider="rule_based")
    ).analyze(item)

    assert insight.signal_tier == SignalTier.actionable
    assert "energy supply" in insight.themes
    assert "shipping risk" in insight.themes
    assert "energy" in insight.affected_markets


def test_auto_provider_prefers_gemini_then_openai_then_ollama_then_rules():
    assert (
        Settings(
            analysis_provider="auto",
            gemini_api_key="gemini-key",
            openai_api_key="openai-key",
            ollama_enabled=True,
        ).resolved_analysis_provider()
        == "gemini"
    )
    assert (
        Settings(
            analysis_provider="auto",
            openai_api_key="openai-key",
        ).resolved_analysis_provider()
        == "openai"
    )
    assert (
        Settings(
            analysis_provider="auto",
            ollama_enabled=True,
        ).resolved_analysis_provider()
        == "ollama"
    )
    assert Settings(analysis_provider="auto").resolved_analysis_provider() == "rule_based"


@pytest.mark.asyncio
async def test_gemini_analysis_placeholder_without_key():
    item = NewsItem(
        title="Market update",
        source="Test",
        url="https://example.com/market-update",
    )

    insight = await EconomicAnalystAgent(Settings(analysis_provider="gemini")).analyze(
        item
    )

    assert insight.signal_tier == SignalTier.fyi
    assert "GEMINI_API_KEY is not set" in insight.rationale


@pytest.mark.asyncio
async def test_openai_analysis_falls_back_without_key():
    item = NewsItem(
        title="Oil shipping risk rises near the Red Sea",
        source="Test",
        url="https://example.com/openai-fallback",
    )

    insight = await EconomicAnalystAgent(Settings(analysis_provider="openai")).analyze(
        item
    )

    assert insight.signal_tier == SignalTier.actionable
    assert "OPENAI_API_KEY is not set" in insight.rationale
    assert "energy supply" in insight.themes


@pytest.mark.asyncio
async def test_ollama_analysis_disabled_falls_back_to_rules():
    item = NewsItem(
        title="Oil shipping risk rises near the Red Sea",
        source="Test",
        url="https://example.com/ollama-fallback",
    )

    insight = await EconomicAnalystAgent(Settings(analysis_provider="ollama")).analyze(
        item
    )

    assert insight.signal_tier == SignalTier.actionable
    assert "OLLAMA_ENABLED is false" in insight.rationale
    assert "energy supply" in insight.themes
