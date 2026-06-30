import sys
from pathlib import Path


def get_project_root() -> Path:
    """返回项目根目录。

    当前文件位于 `src/gmap_collector/common/paths.py`，向上三级即可到达项目根目录。
    PyInstaller 打包后使用 exe 所在目录作为项目根目录，让 `config/`、`data/`、
    `exports/`、`logs/` 和 `drivers/` 可以随发布目录整体迁移。
    统一使用这个函数可以避免不同模块各自拼接相对路径，降低打包和迁移时的路径风险。
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def resolve_project_path(path: str | Path) -> Path:
    """将配置中的相对路径转换为项目根目录下的绝对路径。

    配置文件中保留相对路径，方便整个项目目录迁移；真正访问文件系统时再解析成绝对路径。
    如果传入的已经是绝对路径，则原样返回。
    """
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return get_project_root() / candidate
