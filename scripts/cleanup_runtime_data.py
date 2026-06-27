from __future__ import annotations

import argparse
import shutil
import sqlite3
from pathlib import Path


RUNTIME_FILES = [
    Path("data/app.sqlite3"),
    Path("data/app.sqlite3-wal"),
    Path("data/app.sqlite3-shm"),
]

RUNTIME_DIRECTORIES = [
    Path("outputs"),
    Path("output"),
    Path("debug"),
    Path("tmp"),
    Path("temp"),
    Path("screenshots"),
]

OPTIONAL_BROWSER_CACHE_DIRECTORIES = [
    Path("drivers/selenium-cache"),
]

CLEAN_DIRECTORY_CONTENTS = [
    Path("logs"),
    Path("exports"),
]

KEEP_FILENAMES = {".gitkeep"}
RESET_TABLES = [
    "business_task_hits",
    "businesses",
    "keyword_tasks",
    "task_batches",
]


def cleanup_runtime_data(
    project_root: str | Path,
    include_browser_cache: bool = False,
    reset_locked_database: bool = False,
) -> list[Path]:
    """清理项目运行产物，并返回已清理的相对路径列表。

    该脚本只清理测试和运行过程中生成的数据库、日志、导出和调试输出，不清理
    `keyword.txt`、`keywords` 或配置文件。默认保留浏览器登录缓存；如果需要全新
    测试环境，可以传入 `include_browser_cache=True` 一并清理浏览器用户数据目录。
    GUI 运行时 SQLite 文件可能被当前进程占用，此时可以传入 `reset_locked_database=True`
    清空数据库表内容作为兜底。
    """
    root = Path(project_root).resolve()
    removed_paths: list[Path] = []

    for relative_path in RUNTIME_FILES:
        path = root / relative_path
        if path.exists():
            try:
                path.unlink()
            except PermissionError:
                if reset_locked_database and relative_path == Path("data/app.sqlite3"):
                    reset_sqlite_database(path)
                elif reset_locked_database and relative_path in {Path("data/app.sqlite3-wal"), Path("data/app.sqlite3-shm")}:
                    continue
                else:
                    raise
            removed_paths.append(relative_path)

    for relative_path in RUNTIME_DIRECTORIES:
        path = root / relative_path
        if path.exists():
            shutil.rmtree(path)
            removed_paths.append(relative_path)

    for relative_path in CLEAN_DIRECTORY_CONTENTS:
        directory = root / relative_path
        if not directory.exists():
            continue
        for child in directory.iterdir():
            if child.name in KEEP_FILENAMES:
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
            removed_paths.append(relative_path / child.name)

    if include_browser_cache:
        for relative_path in OPTIONAL_BROWSER_CACHE_DIRECTORIES:
            path = root / relative_path
            if path.exists():
                shutil.rmtree(path)
                removed_paths.append(relative_path)

    return removed_paths


def reset_sqlite_database(database_path: str | Path) -> None:
    """清空 SQLite 业务表，并重置自增序列。

    Windows 下 GUI 程序可能暂时占用 `data/app.sqlite3`，导致文件无法直接删除。
    这个兜底函数只在用户确认清理时使用，用于让数据库回到空表状态。
    """
    path = Path(database_path)
    with sqlite3.connect(path) as connection:
        existing_tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        connection.execute("PRAGMA foreign_keys = OFF")
        for table_name in RESET_TABLES:
            if table_name in existing_tables:
                connection.execute(f"DELETE FROM {table_name}")
        if "sqlite_sequence" in existing_tables:
            placeholders = ",".join("?" for _ in RESET_TABLES)
            connection.execute(
                f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})",
                RESET_TABLES,
            )
        connection.commit()


def main() -> None:
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="清理 GoogleMaps_LeadForge 本地运行产物。")
    parser.add_argument(
        "--project-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="项目根目录，默认自动识别当前脚本所在项目。",
    )
    parser.add_argument(
        "--include-browser-cache",
        action="store_true",
        help="同时清理浏览器用户缓存目录，包含 Google 登录状态。",
    )
    parser.add_argument(
        "--reset-locked-database",
        action="store_true",
        help="数据库文件被占用时清空业务表作为兜底，主要用于 GUI 内部清理。",
    )
    args = parser.parse_args()

    removed_paths = cleanup_runtime_data(
        args.project_root,
        include_browser_cache=args.include_browser_cache,
        reset_locked_database=args.reset_locked_database,
    )
    if not removed_paths:
        print("没有需要清理的运行产物。")
        return

    print("已清理以下运行产物：")
    for relative_path in removed_paths:
        print(f"- {relative_path}")


if __name__ == "__main__":
    main()
