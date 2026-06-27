import pandas as pd

from gmap_collector.common.models import BusinessRecord
from gmap_collector.exporters.business_exporter import export_businesses_to_csv, export_businesses_to_excel
from gmap_collector.storage.database import initialize_database
from gmap_collector.storage.repositories import BusinessRepository


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


def _business_record() -> BusinessRecord:
    """构造测试商家记录。"""
    return BusinessRecord(
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
