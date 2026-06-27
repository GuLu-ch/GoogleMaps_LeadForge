import sqlite3

from gmap_collector.storage.database import initialize_database


def test_initialize_database_creates_required_tables(tmp_path):
    """初始化数据库后，应创建任务、关键词、商家和命中关系表。"""
    database_path = tmp_path / "app.sqlite3"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()

    table_names = {row[0] for row in rows}
    assert {"task_batches", "keyword_tasks", "businesses", "business_task_hits"}.issubset(table_names)
