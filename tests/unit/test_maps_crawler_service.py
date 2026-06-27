import sqlite3

from gmap_collector.browser.base import BrowserEngine, BrowserPageSnapshot
from gmap_collector.services.maps_crawler import MapsCrawlRequest, crawl_maps_search
from gmap_collector.storage.database import initialize_database
from gmap_collector.storage.repositories import BusinessRepository


class FakeBrowserEngine(BrowserEngine):
    """用于单元测试的浏览器引擎。"""

    def __init__(self, html: str):
        self.html = html
        self.opened_urls: list[str] = []
        self.wait_for_results_calls: list[int] = []
        self.scroll_count = 0

    def start(self) -> None:
        pass

    def close(self) -> None:
        pass

    def open_url(self, url: str) -> None:
        self.opened_urls.append(url)

    def wait_for_results(self, timeout_seconds: int = 20) -> bool:
        self.wait_for_results_calls.append(timeout_seconds)
        return True

    def get_snapshot(self) -> BrowserPageSnapshot:
        return BrowserPageSnapshot(html=self.html, current_url=self.opened_urls[-1] if self.opened_urls else "")

    def scroll_results(self) -> None:
        self.scroll_count += 1

    def is_at_results_bottom(self) -> bool:
        return self.scroll_count >= 1


def test_crawl_maps_search_parses_and_persists_businesses(tmp_path):
    """采集服务应打开搜索 URL、解析列表页并写入去重后的 SQLite。"""
    html = """
    <div role="feed">
      <div role="article">
        <a href="https://www.google.com/maps/place/Folie+Studio/data=!4m6">Folie Studio</a>
        <span aria-label="4.8 stars">4.8</span>
        <span aria-label="128 reviews">(128)</span>
        <div>Car wrapping service</div>
        <div>Hauptstrasse 12, Berlin, Germany</div>
        <a href="tel:+493012345678">+49 30 12345678</a>
      </div>
    </div>
    """
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    repository = BusinessRepository(database_path)
    engine = FakeBrowserEngine(html)

    waits: list[tuple[float, float]] = []

    result = crawl_maps_search(
        engine=engine,
        repository=repository,
        request=MapsCrawlRequest(
            search_url="https://www.google.com/maps/search/Car+Wrap+Shop+in+Berlin",
            source_keyword="Car Wrap Shop",
            max_scroll_rounds=3,
            no_new_results_threshold=2,
            scroll_wait_seconds_min=2,
            scroll_wait_seconds_max=5,
            page_initial_wait_seconds=3,
            query_text="Car Wrap Shop in Berlin, Berlin, Germany",
        ),
        wait_for_seconds=lambda minimum, maximum: waits.append((minimum, maximum)),
    )

    businesses = repository.list_businesses()
    assert result.parsed_count == 1
    assert result.saved_count == 1
    assert engine.opened_urls == ["https://www.google.com/maps/search/Car+Wrap+Shop+in+Berlin"]
    assert engine.wait_for_results_calls == [20]
    assert engine.scroll_count == 1
    assert waits == [(3, 3), (2, 5)]
    assert businesses[0]["name"] == "Folie Studio"
    assert businesses[0]["source_keywords"] == "Car Wrap Shop"

    with sqlite3.connect(database_path) as connection:
        hit_count = connection.execute("SELECT COUNT(*) FROM business_task_hits").fetchone()[0]

    assert hit_count == 1
