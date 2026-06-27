import json
from pathlib import Path
from typing import Any

from gmap_collector.config.schemas import (
    AppConfig,
    BrowserConfig,
    CityConfig,
    CountryConfig,
    CrawlerConfig,
    ExportConfig,
    LocationsConfig,
    PathConfig,
    RegionConfig,
)


def _read_json(path: Path) -> dict[str, Any]:
    """读取 JSON 文件并返回字典。

    这里集中处理文件读取，后续如果需要加入配置版本、错误提示或兼容旧字段，只需要改这一处。
    """
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"配置文件必须是 JSON 对象: {path}")

    return data


def load_app_config(path: str | Path) -> AppConfig:
    """读取应用运行配置。"""
    data = _read_json(Path(path))
    browser = data["browser"]
    crawler = data["crawler"]
    paths = data["paths"]
    export = data["export"]

    return AppConfig(
        browser=BrowserConfig(
            default_browser=browser["default_browser"],
            supported_browsers=tuple(browser["supported_browsers"]),
            default_engine=browser["default_engine"],
            supported_engines=tuple(browser["supported_engines"]),
            headless=bool(browser["headless"]),
        ),
        crawler=CrawlerConfig(
            page_initial_wait_seconds=int(crawler["page_initial_wait_seconds"]),
            keyword_wait_seconds_min=int(crawler["keyword_wait_seconds_min"]),
            keyword_wait_seconds_max=int(crawler["keyword_wait_seconds_max"]),
            scroll_wait_seconds_min=int(crawler["scroll_wait_seconds_min"]),
            scroll_wait_seconds_max=int(crawler["scroll_wait_seconds_max"]),
            max_scroll_rounds=int(crawler["max_scroll_rounds"]),
            max_no_new_results_rounds=int(crawler["max_no_new_results_rounds"]),
            page_load_timeout_seconds=int(crawler["page_load_timeout_seconds"]),
            consecutive_failure_pause_threshold=int(crawler["consecutive_failure_pause_threshold"]),
        ),
        paths=PathConfig(
            database=Path(paths["database"]),
            export_dir=Path(paths["export_dir"]),
            log_dir=Path(paths["log_dir"]),
            selenium_cache_dir=Path(paths["selenium_cache_dir"]),
            playwright_browsers_dir=Path(paths["playwright_browsers_dir"]),
        ),
        export=ExportConfig(
            csv_encoding=export["csv_encoding"],
            excel_file_extension=export["excel_file_extension"],
        ),
    )


def load_locations_config(path: str | Path) -> LocationsConfig:
    """读取国家、地区和城市配置。"""
    data = _read_json(Path(path))

    countries: list[CountryConfig] = []
    for country_data in data["countries"]:
        regions: list[RegionConfig] = []
        for region_data in country_data["regions"]:
            cities = tuple(
                CityConfig(name=city_data["name"], search_name=city_data["search_name"])
                for city_data in region_data["cities"]
            )
            regions.append(
                RegionConfig(
                    name=region_data["name"],
                    search_name=region_data["search_name"],
                    cities=cities,
                )
            )

        countries.append(
            CountryConfig(
                name=country_data["name"],
                search_name=country_data["search_name"],
                regions=tuple(regions),
            )
        )

    return LocationsConfig(countries=tuple(countries))
