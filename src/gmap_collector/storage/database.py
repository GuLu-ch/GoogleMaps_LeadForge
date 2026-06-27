import sqlite3
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS task_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    total_keywords INTEGER NOT NULL DEFAULT 0,
    completed_keywords INTEGER NOT NULL DEFAULT 0,
    failed_keywords INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS keyword_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    country_name TEXT NOT NULL,
    country_search_name TEXT NOT NULL,
    region_name TEXT NOT NULL,
    region_search_name TEXT NOT NULL,
    city_name TEXT NOT NULL,
    city_search_name TEXT NOT NULL,
    query_text TEXT NOT NULL,
    search_url TEXT NOT NULL,
    status TEXT NOT NULL,
    failure_reason TEXT NOT NULL DEFAULT '',
    last_run_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES task_batches(id)
);

CREATE TABLE IF NOT EXISTS businesses (
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
);

CREATE TABLE IF NOT EXISTS business_task_hits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL,
    keyword_task_id INTEGER,
    query_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES businesses(id),
    FOREIGN KEY (keyword_task_id) REFERENCES keyword_tasks(id)
);
"""


def initialize_database(database_path: str | Path) -> None:
    """初始化 SQLite 数据库。

    该函数只负责创建目录和表结构，不写入任何业务数据，方便应用启动时反复调用。
    """
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.commit()
