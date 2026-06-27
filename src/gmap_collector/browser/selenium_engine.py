from gmap_collector.browser.base import BrowserEngine, BrowserPageSnapshot


class SeleniumBrowserEngine(BrowserEngine):
    """Selenium 浏览器引擎骨架。

    当前阶段只提供统一接口和生命周期结构。Google Maps 结果列表的具体 DOM 定位
    需要后续在可视化浏览器中确认后再补充，避免提前写死不可靠选择器。
    """

    def __init__(self, browser_name: str = "chrome"):
        self.browser_name = browser_name
        self.driver = None

    def start(self) -> None:
        """启动浏览器。

        实际 Selenium 启动参数会在浏览器调试阶段补充，例如 Chrome/Edge 选择、
        驱动缓存路径和页面加载超时。
        """
        self.driver = None

    def close(self) -> None:
        """关闭 Selenium 浏览器。"""
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    def open_url(self, url: str) -> None:
        """打开 URL。"""
        if self.driver is None:
            raise RuntimeError("Selenium 浏览器尚未启动")
        self.driver.get(url)

    def get_snapshot(self) -> BrowserPageSnapshot:
        """返回页面快照。"""
        if self.driver is None:
            return BrowserPageSnapshot(html="", current_url="")
        return BrowserPageSnapshot(html=self.driver.page_source, current_url=self.driver.current_url)

    def scroll_results(self) -> None:
        """滚动搜索结果列表。

        具体滚动容器需要用户协助确认 DOM 后实现。
        """
        raise NotImplementedError("Google Maps 结果列表滚动逻辑尚未确认 DOM")

    def is_at_results_bottom(self) -> bool:
        """判断是否到底。

        具体判断条件需要用户协助确认 DOM 后实现。
        """
        return False
