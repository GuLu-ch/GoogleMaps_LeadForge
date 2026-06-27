from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BrowserConfig:
    """浏览器配置。

    `default_browser` 控制默认浏览器，`default_engine` 控制默认自动化引擎。
    `headless` 第一版固定为 False，配置字段保留是为了后续扩展，但 GUI 不开放无头模式。
    """

    default_browser: str
    supported_browsers: tuple[str, ...]
    default_engine: str
    supported_engines: tuple[str, ...]
    headless: bool


@dataclass(frozen=True)
class CrawlerConfig:
    """爬取节流和失败策略配置。"""

    page_initial_wait_seconds: int
    keyword_wait_seconds_min: int
    keyword_wait_seconds_max: int
    scroll_wait_seconds_min: int
    scroll_wait_seconds_max: int
    max_scroll_rounds: int
    max_no_new_results_rounds: int
    page_load_timeout_seconds: int
    consecutive_failure_pause_threshold: int


@dataclass(frozen=True)
class PathConfig:
    """项目内路径配置。

    这些路径在配置文件中使用相对路径，便于整体迁移项目目录。
    """

    database: Path
    export_dir: Path
    log_dir: Path
    selenium_cache_dir: Path
    playwright_browsers_dir: Path


@dataclass(frozen=True)
class ExportConfig:
    """导出文件配置。"""

    csv_encoding: str
    excel_file_extension: str


@dataclass(frozen=True)
class AppConfig:
    """应用运行配置总对象。"""

    browser: BrowserConfig
    crawler: CrawlerConfig
    paths: PathConfig
    export: ExportConfig


@dataclass(frozen=True)
class CityConfig:
    """城市配置。"""

    name: str
    search_name: str


@dataclass(frozen=True)
class RegionConfig:
    """地区或州配置。"""

    name: str
    search_name: str
    cities: tuple[CityConfig, ...]


@dataclass(frozen=True)
class CountryConfig:
    """国家配置。"""

    name: str
    search_name: str
    regions: tuple[RegionConfig, ...]


@dataclass(frozen=True)
class LocationsConfig:
    """地区配置总对象。"""

    countries: tuple[CountryConfig, ...]
