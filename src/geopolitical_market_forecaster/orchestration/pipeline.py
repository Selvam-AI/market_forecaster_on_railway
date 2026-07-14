from geopolitical_market_forecaster.agents.analyst import EconomicAnalystAgent
from geopolitical_market_forecaster.agents.governor import GovernorAgent
from geopolitical_market_forecaster.agents.predictor import PredictorAgent
from geopolitical_market_forecaster.agents.scraper import ScraperAgent
from geopolitical_market_forecaster.config import Settings
from geopolitical_market_forecaster.models import GovernanceReview, PipelineResult
from geopolitical_market_forecaster.storage import (
    initialize_database,
    record_audit_event,
    save_economic_insight,
    save_governance_review,
    save_market_forecast,
)


class ForecastPipeline:
    def __init__(self, settings: Settings):
        self.scraper = ScraperAgent(settings)
        self.analyst = EconomicAnalystAgent(settings)
        self.predictor = PredictorAgent()
        self.governor = GovernorAgent()

    async def run(self) -> PipelineResult:
        initialize_database(self.scraper.settings.database_url)
        items = await self.scraper.collect()
        reviews: list[GovernanceReview] = []
        insights_created = 0
        forecasts_created = 0
        reviews_created = 0

        record_audit_event(
            self.scraper.settings.database_url,
            "scraper_handoff",
            f"Collected {len(items)} news items for analysis.",
        )

        for item in items:
            insight = await self.analyst.analyze(item)
            save_economic_insight(self.scraper.settings.database_url, insight)
            insights_created += 1
            record_audit_event(
                self.scraper.settings.database_url,
                "analyst_handoff",
                insight.model_dump_json(),
            )

            forecast = await self.predictor.forecast(insight)
            save_market_forecast(self.scraper.settings.database_url, forecast)
            forecasts_created += 1
            record_audit_event(
                self.scraper.settings.database_url,
                "predictor_handoff",
                forecast.model_dump_json(),
            )

            review = await self.governor.review(forecast)
            save_governance_review(self.scraper.settings.database_url, review)
            reviews_created += 1
            record_audit_event(
                self.scraper.settings.database_url,
                "governor_handoff",
                review.model_dump_json(),
            )
            reviews.append(review)

        return PipelineResult(
            items_collected=len(items),
            insights_created=insights_created,
            forecasts_created=forecasts_created,
            reviews_created=reviews_created,
            reviews=reviews,
        )
