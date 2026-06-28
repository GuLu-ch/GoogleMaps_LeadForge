from pathlib import Path
import sqlite3

from gmap_collector.common.models import BusinessRecord
from gmap_collector.storage.database import initialize_database
from gmap_collector.storage.repositories import BusinessRepository
from gmap_collector.storage.task_repository import KeywordTaskCreate, TaskRepository
from gmap_collector.storage.website_exploration_repository import WebsiteExplorationRepository
from scripts.cleanup_runtime_data import cleanup_runtime_data, reset_sqlite_database


def test_cleanup_runtime_data_removes_runtime_outputs_and_keeps_inputs(tmp_path):
    """清理脚本应删除运行产物，但保留关键词输入和目录占位文件。"""
    (tmp_path / "data").mkdir()
    (tmp_path / "logs").mkdir()
    (tmp_path / "exports").mkdir()
    (tmp_path / "outputs").mkdir()
    (tmp_path / "debug").mkdir()
    (tmp_path / "temp").mkdir()
    (tmp_path / "screenshots").mkdir()

    for relative_path in [
        "data/app.sqlite3",
        "data/app.sqlite3-wal",
        "logs/run.log",
        "exports/result.csv",
        "outputs/page.html",
        "debug/debug.txt",
        "temp/tmp.txt",
        "screenshots/page.png",
    ]:
        path = tmp_path / relative_path
        path.write_text("运行产物", encoding="utf-8")

    for relative_path in ["logs/.gitkeep", "exports/.gitkeep", "keyword.txt"]:
        path = tmp_path / relative_path
        path.write_text("保留文件", encoding="utf-8")

    removed_paths = cleanup_runtime_data(project_root=tmp_path)

    assert (tmp_path / "keyword.txt").exists()
    assert (tmp_path / "logs/.gitkeep").exists()
    assert (tmp_path / "exports/.gitkeep").exists()
    assert not (tmp_path / "data/app.sqlite3").exists()
    assert not (tmp_path / "logs/run.log").exists()
    assert not (tmp_path / "outputs").exists()
    assert Path("data/app.sqlite3") in removed_paths
    assert Path("outputs") in removed_paths


def test_cleanup_runtime_data_can_remove_browser_cache_when_requested(tmp_path):
    """需要全新测试环境时，清理函数应可选删除浏览器用户缓存。"""
    browser_cache_dir = tmp_path / "drivers" / "selenium-cache" / "chrome"
    browser_cache_dir.mkdir(parents=True)
    (browser_cache_dir / "Cookies").write_text("登录缓存", encoding="utf-8")

    removed_paths = cleanup_runtime_data(project_root=tmp_path, include_browser_cache=True)

    assert not (tmp_path / "drivers" / "selenium-cache").exists()
    assert Path("drivers/selenium-cache") in removed_paths


def test_reset_locked_database_clears_website_exploration_tables(tmp_path):
    """数据库文件被占用只能清表时，也必须清空官网探索批次和探索任务。"""
    database_path = tmp_path / "data" / "app.sqlite3"
    initialize_database(database_path)
    maps_repository = TaskRepository(database_path)
    business_repository = BusinessRepository(database_path)
    exploration_repository = WebsiteExplorationRepository(database_path)

    maps_batch_id = maps_repository.create_batch("清理兜底测试")
    maps_repository.add_keyword_tasks(
        maps_batch_id,
        [
            KeywordTaskCreate(
                keyword="Car Wrap Shop",
                country_name="德国",
                country_search_name="Germany",
                region_name="柏林州",
                region_search_name="Berlin",
                city_name="柏林",
                city_search_name="Berlin",
                query_text="Car Wrap Shop in Berlin, Berlin, Germany",
                search_url="https://www.google.com/maps/search/Car+Wrap+Shop+in+Berlin",
            )
        ],
    )
    keyword_task = maps_repository.list_keyword_tasks(maps_batch_id)[0]
    business_repository.upsert_business(
        BusinessRecord(
            name="Alpha Wrap",
            address="Street 1",
            phone="+49 111",
            website="https://alpha.example.com",
            rating="4.8",
            review_count="120",
            category="Car wrap shop",
            google_maps_url="https://maps.google.com/?cid=cleanup-fallback",
            source_keyword="Car Wrap Shop",
        ),
        keyword_task_id=keyword_task["id"],
        query_text=keyword_task["query_text"],
    )
    exploration_repository.create_batch_from_maps_task(maps_batch_id)

    reset_sqlite_database(database_path)

    with sqlite3.connect(database_path) as connection:
        for table_name in [
            "website_exploration_tasks",
            "website_exploration_batches",
            "business_task_hits",
            "businesses",
            "keyword_tasks",
            "task_batches",
        ]:
            count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            assert count == 0
