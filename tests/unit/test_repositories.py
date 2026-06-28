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


def test_business_repository_returns_raw_hit_and_deduped_counts(tmp_path):
    """商家仓储应能返回原始命中数和去重商家数，供任务执行页展示。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    repository = BusinessRepository(database_path)
    record = BusinessRecord(
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

    repository.upsert_business(record, keyword_task_id=1, query_text="Car Wrap Shop in Berlin")
    repository.upsert_business(record, keyword_task_id=2, query_text="PPF in Berlin")

    assert repository.get_business_stats() == {
        "raw_hits": 2,
        "deduped_businesses": 1,
    }


def test_business_repository_returns_website_exploration_fields(tmp_path):
    """结果管理读取商家时，应包含官网探索预留字段。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    repository = BusinessRepository(database_path)
    repository.upsert_business(
        BusinessRecord(
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
    )

    business = repository.list_businesses()[0]

    assert business["explored_phone"] == ""
    assert business["emails"] == ""
    assert business["instagram"] == ""
    assert business["tiktok"] == ""
    assert business["twitter_x"] == ""
    assert business["facebook"] == ""
    assert business["linkedin"] == ""
    assert business["youtube"] == ""
    assert business["whatsapp"] == ""
    assert business["seo_keywords"] == ""
    assert business["website_exploration_status"] == "未探索"
    assert business["website_explored_at"] == ""
