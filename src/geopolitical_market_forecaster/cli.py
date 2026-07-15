import argparse
import asyncio
import json

from geopolitical_market_forecaster.config import get_settings
from geopolitical_market_forecaster.ingestion import NewsIngestionService
from geopolitical_market_forecaster.models import IngestionResult
from geopolitical_market_forecaster.orchestration.pipeline import ForecastPipeline
from geopolitical_market_forecaster.storage import (
    count_rows,
    initialize_database,
    list_recent_news_items,
    record_audit_event,
    save_news_items,
)


async def run_pipeline(verbose: bool) -> None:
    settings = get_settings()
    initialize_database(settings.database_url)
    result = await ForecastPipeline(settings).run()
    if verbose:
        print(json.dumps(result.model_dump(mode="json"), indent=2))
        return

    summary = {
        "items_collected": result.items_collected,
        "insights_created": result.insights_created,
        "forecasts_created": result.forecasts_created,
        "reviews_created": result.reviews_created,
        "approved": sum(1 for review in result.reviews if review.approved),
        "flagged": sum(1 for review in result.reviews if review.flags),
    }
    print(json.dumps(summary, indent=2))


async def ingest_news(source: str) -> None:
    settings = get_settings()
    initialize_database(settings.database_url)
    source_used, items, errors = await NewsIngestionService(settings).fetch(source)
    inserted, skipped = save_news_items(settings.database_url, items)
    result = IngestionResult(
        source=source_used,
        fetched=len(items),
        inserted=inserted,
        skipped=skipped,
        errors=errors,
    )
    record_audit_event(
        settings.database_url,
        "news_ingestion",
        result.model_dump_json(),
    )
    print(json.dumps(result.model_dump(mode="json"), indent=2))


def show_news(limit: int) -> None:
    settings = get_settings()
    initialize_database(settings.database_url)
    print(json.dumps(list_recent_news_items(settings.database_url, limit), indent=2))


def show_status() -> None:
    settings = get_settings()
    initialize_database(settings.database_url)
    status = {
        "news_items": count_rows(settings.database_url, "news_items"),
        "economic_insights": count_rows(settings.database_url, "economic_insights"),
        "market_forecasts": count_rows(settings.database_url, "market_forecasts"),
        "governance_reviews": count_rows(settings.database_url, "governance_reviews"),
        "audit_events": count_rows(settings.database_url, "audit_events"),
    }
    print(json.dumps(status, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SGX Geopolitical Forecaster CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    pipeline_parser = subparsers.add_parser(
        "run-pipeline",
        help="Run the full forecast pipeline.",
    )
    pipeline_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print full nested pipeline output.",
    )

    ingest_parser = subparsers.add_parser("ingest-news", help="Fetch and store news.")
    ingest_parser.add_argument(
        "--source",
        choices=["auto", "guardian", "newsapi", "rss"],
        default="auto",
        help="News source to use.",
    )

    show_parser = subparsers.add_parser("show-news", help="Show stored news items.")
    show_parser.add_argument("--limit", type=int, default=10)
    subparsers.add_parser("show-status", help="Show database table counts.")

    args = parser.parse_args()
    if args.command == "run-pipeline":
        asyncio.run(run_pipeline(args.verbose))
    elif args.command == "ingest-news":
        asyncio.run(ingest_news(args.source))
    elif args.command == "show-news":
        show_news(args.limit)
    elif args.command == "show-status":
        show_status()


if __name__ == "__main__":
    main()
