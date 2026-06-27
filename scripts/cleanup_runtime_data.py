from __future__ import annotations

import argparse
import shutil
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

CLEAN_DIRECTORY_CONTENTS = [
    Path("logs"),
    Path("exports"),
]

KEEP_FILENAMES = {".gitkeep"}


def cleanup_runtime_data(project_root: str | Path) -> list[Path]:
    """清理项目运行产物，并返回已清理的相对路径列表。

    该脚本只清理测试和运行过程中生成的数据库、日志、导出和调试输出，不清理
    `keyword.txt`、`keywords`、配置文件或浏览器登录缓存。
    """
    root = Path(project_root).resolve()
    removed_paths: list[Path] = []

    for relative_path in RUNTIME_FILES:
        path = root / relative_path
        if path.exists():
            path.unlink()
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

    return removed_paths


def main() -> None:
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="清理 GoogleMaps_LeadForge 本地运行产物。")
    parser.add_argument(
        "--project-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="项目根目录，默认自动识别当前脚本所在项目。",
    )
    args = parser.parse_args()

    removed_paths = cleanup_runtime_data(args.project_root)
    if not removed_paths:
        print("没有需要清理的运行产物。")
        return

    print("已清理以下运行产物：")
    for relative_path in removed_paths:
        print(f"- {relative_path}")


if __name__ == "__main__":
    main()
