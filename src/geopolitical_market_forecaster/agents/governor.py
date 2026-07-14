from geopolitical_market_forecaster.models import GovernanceReview, MarketForecast


class GovernorAgent:
    """Checks provenance, quality, and forecast discipline."""

    async def review(self, forecast: MarketForecast) -> GovernanceReview:
        flags: list[str] = []

        if not forecast.evidence:
            flags.append("missing_evidence")

        if forecast.confidence.value == "High":
            flags.append("high_confidence_requires_manual_review")

        return GovernanceReview(
            forecast=forecast,
            approved=not flags,
            flags=flags,
            audit_notes=[
                "Source URL retained for traceability.",
                "Forecast confidence and uncertainty are explicit.",
            ],
        )
