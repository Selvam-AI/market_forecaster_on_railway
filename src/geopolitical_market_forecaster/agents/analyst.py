import json

import httpx

from geopolitical_market_forecaster.config import Settings
from geopolitical_market_forecaster.error_logging import append_error_log
from geopolitical_market_forecaster.models import (
    EconomicInsight,
    NewsItem,
    SignalTier,
)


class EconomicAnalystAgent:
    """Turns news items into market-oriented insights."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings

    async def analyze(self, item: NewsItem) -> EconomicInsight:
        provider = (
            self.settings.resolved_analysis_provider()
            if self.settings
            else "rule_based"
        )
        if provider == "gemini":
            return await self._analyze_with_gemini(item)
        if provider == "openai":
            return await self._analyze_with_openai(item)
        if provider == "ollama":
            return await self._analyze_with_ollama(item)
        return self._analyze_with_rules(item)

    def _analyze_with_rules(self, item: NewsItem) -> EconomicInsight:
        text = f"{item.title} {item.summary or ''} {item.raw_text or ''}".lower()
        themes: list[str] = []
        affected_markets: list[str] = []

        if any(term in text for term in ["oil", "gas", "energy", "opec"]):
            themes.append("energy supply")
            affected_markets.append("energy")
        if any(term in text for term in ["shipping", "strait", "red sea", "suez"]):
            themes.append("shipping risk")
            affected_markets.append("shipping")
        if any(term in text for term in ["sanction", "tariff", "trade"]):
            themes.append("trade policy")
            affected_markets.append("currencies")
        if any(term in text for term in ["war", "missile", "attack", "tension"]):
            themes.append("geopolitical risk")
            affected_markets.append("regional equities")

        if not themes:
            themes = ["market sentiment"]
        if not affected_markets:
            affected_markets = ["regional equities"]

        signal_tier = SignalTier.actionable if len(themes) >= 2 else SignalTier.fyi

        return EconomicInsight(
            news_item=item,
            signal_tier=signal_tier,
            themes=themes,
            affected_markets=affected_markets,
            rationale="Rule-based analysis from keyword signals in the article title, summary, and body text.",
        )

    async def _analyze_with_gemini(self, item: NewsItem) -> EconomicInsight:
        if not self.settings or not self.settings.gemini_api_key:
            insight = await self._fallback_to_ollama_or_rules(item)
            insight.rationale = (
                "Gemini analysis was selected, but GEMINI_API_KEY is not set. "
                f"Fell back safely. {insight.rationale}"
            )
            return insight

        return EconomicInsight(
            news_item=item,
            signal_tier=SignalTier.fyi,
            themes=["market sentiment"],
            affected_markets=["regional equities"],
            rationale=(
                f"Gemini provider placeholder configured for {self.settings.gemini_model}; "
                "LLM prompt execution will be implemented in a later step."
            ),
        )

    async def _analyze_with_openai(self, item: NewsItem) -> EconomicInsight:
        if not self.settings or not self.settings.openai_api_key:
            insight = await self._fallback_to_ollama_or_rules(item)
            insight.rationale = (
                "OpenAI analysis was selected, but OPENAI_API_KEY is not set. "
                f"Fell back safely. {insight.rationale}"
            )
            return insight

        try:
            content = await self._request_openai_analysis(item)
            payload = json.loads(content)
            return self._insight_from_llm_payload(item, payload)
        except Exception as exc:
            append_error_log(
                self.settings.error_log_path,
                "openai-analysis",
                f"{type(exc).__name__}: {exc}",
            )
            insight = await self._fallback_to_ollama_or_rules(item)
            insight.rationale = (
                "OpenAI analysis was unavailable or returned unusable output. "
                f"Fell back safely. {insight.rationale}"
            )
            return insight

    async def _request_openai_analysis(self, item: NewsItem) -> str:
        article_text = "\n".join(
            part
            for part in [item.title, item.summary or "", item.raw_text or ""]
            if part
        )
        prompt = (
            "Analyze this geopolitical news item for market relevance. "
            "Return only JSON with keys signal_tier, themes, affected_markets, "
            "and rationale. signal_tier must be one of Actionable, FYI, or Noise. "
            "Keep rationale to one concise sentence.\n\n"
            f"Source: {item.source}\n"
            f"Region: {item.region}\n"
            f"Article:\n{article_text[:4000]}"
        )
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.settings.openai_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a careful economic analyst. Separate evidence "
                        "from inference and avoid unsupported certainty."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]

    async def _fallback_to_ollama_or_rules(self, item: NewsItem) -> EconomicInsight:
        if self.settings and self.settings.ollama_enabled:
            return await self._analyze_with_ollama(item)
        return self._analyze_with_rules(item)

    async def _analyze_with_ollama(self, item: NewsItem) -> EconomicInsight:
        if not self.settings or not self.settings.ollama_enabled:
            insight = self._analyze_with_rules(item)
            insight.rationale = (
                "Ollama analysis was selected, but OLLAMA_ENABLED is false. "
                f"Fell back to rules. {insight.rationale}"
            )
            return insight

        try:
            content = await self._request_ollama_analysis(item)
            payload = json.loads(content)
            insight = self._insight_from_llm_payload(item, payload)
            insight.rationale = insight.rationale.replace(
                "OpenAI analysis:",
                "Ollama analysis:",
                1,
            )
            return insight
        except Exception as exc:
            append_error_log(
                self.settings.error_log_path,
                "ollama-analysis",
                f"{type(exc).__name__}: {exc}",
            )
            insight = self._analyze_with_rules(item)
            insight.rationale = (
                "Ollama analysis was unavailable or returned unusable output. "
                f"Fell back to rules. {insight.rationale}"
            )
            return insight

    async def _request_ollama_analysis(self, item: NewsItem) -> str:
        article_text = "\n".join(
            part
            for part in [item.title, item.summary or "", item.raw_text or ""]
            if part
        )
        prompt = (
            "Analyze this geopolitical news item for market relevance. "
            "Return only JSON with keys signal_tier, themes, affected_markets, "
            "and rationale. signal_tier must be one of Actionable, FYI, or Noise. "
            "Keep rationale to one concise sentence.\n\n"
            f"Source: {item.source}\n"
            f"Region: {item.region}\n"
            f"Article:\n{article_text[:4000]}"
        )
        body = {
            "model": self.settings.ollama_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a careful economic analyst. Separate evidence "
                        "from inference and avoid unsupported certainty."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "format": "json",
            "stream": False,
        }
        base_url = self.settings.ollama_base_url.rstrip("/")
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{base_url}/api/chat", json=body)
            response.raise_for_status()
            data = response.json()
        return data["message"]["content"]

    def _insight_from_llm_payload(
        self,
        item: NewsItem,
        payload: dict[str, object],
    ) -> EconomicInsight:
        signal_tier = self._parse_signal_tier(payload.get("signal_tier"))
        themes = self._string_list(payload.get("themes")) or ["market sentiment"]
        affected_markets = self._string_list(payload.get("affected_markets")) or [
            "regional equities"
        ]
        rationale = payload.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            rationale = "LLM analysis returned market relevance signals."
        return EconomicInsight(
            news_item=item,
            signal_tier=signal_tier,
            themes=themes,
            affected_markets=affected_markets,
            rationale=f"OpenAI analysis: {rationale.strip()}",
        )

    def _parse_signal_tier(self, value: object) -> SignalTier:
        if isinstance(value, str):
            normalized = value.strip().lower()
            for tier in SignalTier:
                if normalized in {tier.value.lower(), tier.name.lower()}:
                    return tier
        return SignalTier.fyi

    def _string_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
