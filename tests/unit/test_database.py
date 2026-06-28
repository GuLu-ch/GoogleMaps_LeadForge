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
    assert {
        "task_batches",
        "keyword_tasks",
        "businesses",
        "business_task_hits",
        "website_exploration_batches",
        "website_exploration_tasks",
    }.issubset(table_names)


def test_initialize_database_adds_website_exploration_columns_to_existing_businesses(tmp_path):
    """旧数据库升级后，商家主表应具备官网探索结果预留字段。"""
    database_path = tmp_path / "app.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                website TEXT NOT NULL DEFAULT '',
                rating TEXT NOT NULL DEFAULT '',
                review_count TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT '',
                google_maps_url TEXT NOT NULL UNIQUE,
                source_keywords TEXT NOT NULL DEFAULT '',
                first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(businesses)").fetchall()}

    assert {
        "explored_phone",
        "emails",
        "instagram",
        "tiktok",
        "twitter_x",
        "facebook",
        "linkedin",
        "youtube",
        "whatsapp",
        "seo_keywords",
        "website_exploration_status",
        "website_explored_at",
    }.issubset(columns)
