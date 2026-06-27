from pathlib import Path

from scripts.open_login_browser import open_login_browser


def test_open_login_browser_uses_shared_selenium_cache():
    """登录浏览器应使用采集任务同一套 Selenium 用户数据目录。"""
    created_engines = []

    class FakeEngine:
        """测试用浏览器引擎，避免单元测试真的打开浏览器。"""

        def __init__(self, browser_name, page_load_timeout_seconds, cache_dir):
            self.browser_name = browser_name
            self.page_load_timeout_seconds = page_load_timeout_seconds
            self.cache_dir = Path(cache_dir)
            self.opened_url = ""
            self.closed = False
            created_engines.append(self)

        def start(self):
            pass

        def open_url(self, url):
            self.opened_url = url

        def close(self):
            self.closed = True

    open_login_browser(
        browser_name="chrome",
        login_url="https://accounts.google.com/",
        wait_for_close=lambda: "",
        engine_factory=FakeEngine,
    )

    assert len(created_engines) == 1
    assert created_engines[0].browser_name == "chrome"
    assert created_engines[0].cache_dir.parts[-3:] == ("drivers", "selenium-cache", "chrome")
    assert created_engines[0].opened_url == "https://accounts.google.com/"
    assert created_engines[0].closed is True
