import pandas as pd

from gmap_collector.common.models import BusinessRecord
from gmap_collector.exporters.business_exporter import export_businesses_to_csv, export_businesses_to_excel
from gmap_collector.storage.database import initialize_database
from gmap_collector.storage.repositories import BusinessRepository
from gmap_collector.storage.task_repository import KeywordTaskCreate, TaskRepository


def test_export_businesses_to_csv_reads_deduplicated_database_rows(tmp_path):
    """CSV 导出应从 SQLite 去重结果读取，并保留中文表头。"""
    database_path = tmp_path / "app.sqlite3"
    output_path = tmp_path / "businesses.csv"
    initialize_database(database_path)
    repository = BusinessRepository(database_path)
    repository.upsert_business(_business_record())

    export_businesses_to_csv(database_path=database_path, output_path=output_path)

    exported = pd.read_csv(output_path, encoding="utf-8-sig")
    assert list(exported.columns) == [
        "商家名称",
        "地址",
        "电话",
        "官网探索电话",
        "Email",
        "Instagram",
        "TikTok",
        "Twitter / X",
        "Facebook",
        "LinkedIn",
        "YouTube",
        "WhatsApp",
        "SEO Keywords",
        "官网探索状态",
        "官网探索时间",
        "官网",
        "评分",
        "评论数量",
        "商家分类",
        "Google Maps 链接",
        "来源关键词",
        "首次采集时间",
        "最后更新时间",
    ]
    assert exported.iloc[0]["商家名称"] == "Example Wrap"
    assert exported.iloc[0]["官网探索状态"] == "未探索"


def test_export_businesses_to_excel_reads_deduplicated_database_rows(tmp_path):
    """Excel 导出应从 SQLite 去重结果读取。"""
    database_path = tmp_path / "app.sqlite3"
    output_path = tmp_path / "businesses.xlsx"
    initialize_database(database_path)
    repository = BusinessRepository(database_path)
    repository.upsert_business(_business_record())

    export_businesses_to_excel(database_path=database_path, output_path=output_path)

    exported = pd.read_excel(output_path)
    assert exported.iloc[0]["Google Maps 链接"] == "https://maps.google.com/?cid=1"


def test_export_businesses_to_csv_can_filter_by_task_batch(tmp_path):
    """CSV 导出应支持只导出某个 Google Maps 任务批次命中的商家。"""
    database_path = tmp_path / "app.sqlite3"
    output_path = tmp_path / "task_businesses.csv"
    initialize_database(database_path)
    task_repository = TaskRepository(database_path)
    business_repository = BusinessRepository(database_path)
    first_batch_id = task_repository.create_batch("第一任务")
    second_batch_id = task_repository.create_batch("第二任务")
    task_repository.add_keyword_tasks(first_batch_id, [_keyword_task("Car Wrap Shop", "Berlin")])
    task_repository.add_keyword_tasks(second_batch_id, [_keyword_task("PPF", "Munich")])
    first_task = task_repository.list_keyword_tasks(first_batch_id)[0]
    second_task = task_repository.list_keyword_tasks(second_batch_id)[0]
    business_repository.upsert_business(
        _business_record_with_name("Alpha Wrap", "https://maps.google.com/?cid=1"),
        keyword_task_id=first_task["id"],
        query_text=first_task["query_text"],
    )
    business_repository.upsert_business(
        _business_record_with_name("Beta Wrap", "https://maps.google.com/?cid=2"),
        keyword_task_id=second_task["id"],
        query_text=second_task["query_text"],
    )

    export_businesses_to_csv(database_path=database_path, output_path=output_path, batch_id=second_batch_id)

    exported = pd.read_csv(output_path, encoding="utf-8-sig")
    assert list(exported["商家名称"]) == ["Beta Wrap"]


def _business_record() -> BusinessRecord:
    """构造测试商家记录。"""
    return _business_record_with_name("Example Wrap", "https://maps.google.com/?cid=1")


def _business_record_with_name(name: str, google_maps_url: str) -> BusinessRecord:
    """构造带指定名称和链接的商家记录。"""
    return BusinessRecord(
        name=name,
        address="Street 1",
        phone="+49 111",
        website="https://example.com",
        rating="4.8",
        review_count="120",
        category="Car wrap shop",
        google_maps_url=google_maps_url,
        source_keyword="Car Wrap Shop",
    )


def _keyword_task(keyword: str, city: str) -> KeywordTaskCreate:
    """构造关键词任务。"""
    return KeywordTaskCreate(
        keyword=keyword,
        country_name="德国",
        country_search_name="Germany",
        region_name="测试州",
        region_search_name="Test Region",
        city_name=city,
        city_search_name=city,
        query_text=f"{keyword} in {city}, Test Region, Germany",
        search_url=f"https://www.google.com/maps/search/{keyword.replace(' ', '+')}+in+{city}",
    )
