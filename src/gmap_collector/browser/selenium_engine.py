from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import JavascriptException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from gmap_collector.browser.base import BrowserEngine, BrowserPageSnapshot


class SeleniumBrowserEngine(BrowserEngine):
    """Selenium 浏览器引擎。

    第一版使用可视化浏览器，便于观察 Google Maps DOM 和风控状态。
    """

    def __init__(
        self,
        browser_name: str = "chrome",
        page_load_timeout_seconds: int = 60,
        cache_dir: str | Path | None = None,
    ):
        self.browser_name = browser_name
        self.page_load_timeout_seconds = page_load_timeout_seconds
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.driver: WebDriver | None = None

    def start(self) -> None:
        """启动浏览器。"""
        if self.browser_name.lower() == "edge":
            options = EdgeOptions()
            self._apply_common_options(options)
            self.driver = webdriver.Edge(options=options)
        else:
            options = ChromeOptions()
            self._apply_common_options(options)
            self.driver = webdriver.Chrome(options=options)

        self.driver.set_page_load_timeout(self.page_load_timeout_seconds)

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
        try:
            html = str(self.driver.execute_script("return document.documentElement.outerHTML;"))
        except (JavascriptException, WebDriverException):
            html = self.driver.page_source
        return BrowserPageSnapshot(html=html, current_url=self.driver.current_url)

    def scroll_results(self) -> None:
        """滚动搜索结果列表。"""
        if self.driver is None:
            raise RuntimeError("Selenium 浏览器尚未启动")

        self.driver.execute_script(
            """
            const feed = document.querySelector('div[role="feed"]');
            const target = feed || document.scrollingElement || document.documentElement;
            target.scrollBy(0, Math.max(target.clientHeight, 900));
            """
        )

    def is_at_results_bottom(self) -> bool:
        """判断是否到底。

        Google Maps 有时不会直接暴露固定底部标识，所以这里使用滚动位置兜底判断。
        """
        if self.driver is None:
            return False

        try:
            return bool(
                self.driver.execute_script(
                    """
                    const feed = document.querySelector('div[role="feed"]');
                    const target = feed || document.scrollingElement || document.documentElement;
                    return Math.ceil(target.scrollTop + target.clientHeight) >= target.scrollHeight;
                    """
                )
            )
        except (JavascriptException, WebDriverException):
            return False

    def save_screenshot(self, path: str | Path) -> None:
        """保存当前浏览器截图，用于 DOM 诊断。"""
        if self.driver is None:
            raise RuntimeError("Selenium 浏览器尚未启动")
        self.driver.save_screenshot(str(path))

    def wait_for_results(self, timeout_seconds: int = 20) -> bool:
        """等待 Google Maps 结果列表或商家链接出现。"""
        if self.driver is None:
            raise RuntimeError("Selenium 浏览器尚未启动")

        try:
            WebDriverWait(self.driver, timeout_seconds).until(
                lambda driver: driver.execute_script(
                    """
                    return Boolean(
                        document.querySelector('div[role="feed"]')
                        || document.querySelector('a[href*="/maps/place/"]')
                        || document.querySelector('[data-result-index]')
                    );
                    """
                )
            )
            return True
        except TimeoutException:
            return False

    def _apply_common_options(self, options) -> None:
        """应用 Chrome 和 Edge 共用启动参数。"""
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--lang=en-US")
        if self.cache_dir is not None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            options.add_argument(f"--user-data-dir={self.cache_dir}")
