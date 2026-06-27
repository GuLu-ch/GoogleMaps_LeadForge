from pathlib import Path

from gmap_collector.config.loader import load_app_config, load_locations_config


def test_load_app_config_reads_runtime_settings():
    """读取运行配置时，应能拿到浏览器、爬取参数和项目内路径配置。"""
    config = load_app_config(Path("config/app_config.json"))

    assert config.browser.default_browser == "chrome"
    assert config.browser.default_engine == "selenium"
    assert config.browser.headless is False
    assert config.crawler.max_no_new_results_rounds == 3
    assert config.crawler.consecutive_failure_pause_threshold == 3
    assert config.paths.database == Path("data/app.sqlite3")
    assert config.paths.playwright_browsers_dir == Path("drivers/playwright-browsers")


def test_load_locations_config_reads_germany_regions_and_cities():
    """读取全国家地区配置时，应能按搜索名找到德国和城市。"""
    config = load_locations_config(Path("config/locations.json"))

    germany = next(country for country in config.countries if country.search_name == "Germany")

    assert germany.name == "德国"
    assert germany.search_name == "Germany"
    assert len(germany.regions) >= 10
    assert any(region.search_name == "Baden-Württemberg" for region in germany.regions)
    assert any(
        city.search_name == "Biberach"
        for region in germany.regions
        for city in region.cities
    )
