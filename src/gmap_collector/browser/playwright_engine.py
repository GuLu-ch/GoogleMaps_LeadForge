from gmap_collector.browser.base import BrowserEngine, BrowserPageSnapshot


class PlaywrightBrowserEngine(BrowserEngine):
    """Playwright 浏览器引擎骨架。

    该类为后续扩展预留统一接口，第一阶段不写死 Google Maps DOM 选择器。
    """

    def __init__(self, browser_name: str = "chromium"):
        self.browser_name = browser_name
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self) -> None:
        """启动 Playwright 浏览器。

        实际启动逻辑会在浏览器调试阶段补充，并使用项目内 Playwright 浏览器缓存。
        """
        self.playwright = None
        self.browser = None
        self.page = None

    def close(self) -> None:
        """关闭 Playwright 浏览器。"""
        if self.browser is not None:
            self.browser.close()
        if self.playwright is not None:
            self.playwright.stop()
        self.playwright = None
        self.browser = None
        self.page = None

    def open_url(self, url: str) -> None:
        """打开 URL。"""
        if self.page is None:
            raise RuntimeError("Playwright 浏览器尚未启动")
        self.page.goto(url)

    def get_snapshot(self) -> BrowserPageSnapshot:
        """返回页面快照。"""
        if self.page is None:
            return BrowserPageSnapshot(html="", current_url="")
        return BrowserPageSnapshot(html=self.page.content(), current_url=self.page.url)

    def scroll_results(self) -> None:
        """滚动搜索结果列表。"""
        raise NotImplementedError("Google Maps 结果列表滚动逻辑尚未确认 DOM")

    def is_at_results_bottom(self) -> bool:
        """判断是否到底。"""
        return False
