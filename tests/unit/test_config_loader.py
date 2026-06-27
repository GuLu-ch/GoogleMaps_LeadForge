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
    """读取地区配置时，应能拿到德国、至少 10 个地区和测试城市。"""
    config = load_locations_config(Path("config/locations.de.json"))

    germany = config.countries[0]

    assert germany.name == "德国"
    assert germany.search_name == "Germany"
    assert len(germany.regions) >= 10
    assert germany.regions[0].name == "巴登-符腾堡州"
    assert germany.regions[0].cities[1].name == "比伯拉赫"
    assert germany.regions[0].cities[1].search_name == "Biberach"
