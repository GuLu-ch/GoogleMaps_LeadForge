import sqlite3

from gmap_collector.common.models import BusinessRecord
from gmap_collector.storage.database import initialize_database
from gmap_collector.storage.repositories import BusinessRepository


def test_upsert_business_deduplicates_by_google_maps_url_and_merges_keywords(tmp_path):
    """同一 Google Maps 链接重复写入时，应只保留一条商家并合并来源关键词。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    repository = BusinessRepository(database_path)

    first = BusinessRecord(
        name="Example Wrap",
        address="Street 1",
        phone="+49 111",
        website="https://example.com",
        rating="4.8",
        review_count="120",
        category="Car wrap shop",
        google_maps_url="https://maps.google.com/?cid=1",
        source_keyword="Car Wrap Shop",
    )
    second = BusinessRecord(
        name="Example Wrap",
        address="Street 1",
        phone="+49 111",
        website="https://example.com",
        rating="4.8",
        review_count="120",
        category="Car wrap shop",
        google_maps_url="https://maps.google.com/?cid=1",
        source_keyword="PPF",
    )

    first_id = repository.upsert_business(first)
    second_id = repository.upsert_business(second)
    businesses = repository.list_businesses()

    assert first_id == second_id
    assert len(businesses) == 1
    assert businesses[0]["source_keywords"] == "Car Wrap Shop,PPF"

    with sqlite3.connect(database_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]

    assert count == 1
