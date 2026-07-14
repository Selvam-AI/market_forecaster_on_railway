from geopolitical_market_forecaster.models import NewsItem
from geopolitical_market_forecaster.storage import (
    count_rows,
    initialize_database,
    list_recent_news_items,
    load_recent_news_items,
    save_news_items,
)


def test_save_news_items_deduplicates_by_url(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    initialize_database(database_url)

    item = NewsItem(
        title="Shipping risk rises",
        source="Example",
        url="https://example.com/story",
        summary="Summary",
    )

    inserted, skipped = save_news_items(database_url, [item, item])
    rows = list_recent_news_items(database_url)

    assert inserted == 1
    assert skipped == 1
    assert len(rows) == 1
    assert rows[0]["title"] == "Shipping risk rises"
    assert count_rows(database_url, "news_items") == 1


def test_load_recent_news_items_returns_models(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    initialize_database(database_url)
    save_news_items(
        database_url,
        [
            NewsItem(
                title="Stored item",
                source="Example",
                url="https://example.com/stored",
                summary="Stored summary",
            )
        ],
    )

    items = load_recent_news_items(database_url)

    assert len(items) == 1
    assert items[0].title == "Stored item"
