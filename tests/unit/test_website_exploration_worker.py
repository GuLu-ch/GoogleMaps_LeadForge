from gmap_collector.gui import website_exploration_worker as worker_module
from gmap_collector.gui.website_exploration_worker import WebsiteExplorationWorker


def test_website_exploration_worker_browser_fallback_fetches_html_and_closes_engine(tmp_path, monkeypatch):
    """官网探索 Worker 的浏览器兜底应复用缓存目录，并在结束时关闭浏览器。"""

    class FakeEngine:
        """测试用浏览器引擎，避免单元测试打开真实浏览器。"""

        instances = []

        def __init__(self, browser_name, page_load_timeout_seconds, cache_dir):
            self.browser_name = browser_name
            self.page_load_timeout_seconds = page_load_timeout_seconds
            self.cache_dir = cache_dir
            self.started = False
            self.opened_urls = []
            self.wait_timeouts = []
            self.closed = False
            FakeEngine.instances.append(self)

        def start(self):
            self.started = True

        def open_url(self, url):
            self.opened_urls.append(url)

        def wait_for_page_ready(self, timeout_seconds):
            self.wait_timeouts.append(timeout_seconds)
            return True

        def get_snapshot(self):
            class Snapshot:
                html = "<html><body>sales@example-wrap.de</body></html>"

            return Snapshot()

        def close(self):
            self.closed = True

    monkeypatch.setattr(worker_module, "SeleniumBrowserEngine", FakeEngine)
    worker = WebsiteExplorationWorker(
        batch_id=1,
        database_path=tmp_path / "app.sqlite3",
        max_depth=1,
        max_pages=3,
        timeout_seconds=8,
        browser_name="chrome",
        selenium_cache_dir=tmp_path / "drivers" / "selenium-cache",
    )

    html = worker._fetch_with_browser("https://alpha.example.com", 8)
    worker.engine.close()

    engine = FakeEngine.instances[0]
    assert html == "<html><body>sales@example-wrap.de</body></html>"
    assert engine.started is True
    assert engine.browser_name == "chrome"
    assert engine.page_load_timeout_seconds == 8
    assert engine.cache_dir.parts[-3:] == ("drivers", "selenium-cache", "chrome")
    assert engine.opened_urls == ["https://alpha.example.com"]
    assert engine.wait_timeouts == [8]
    assert engine.closed is True
