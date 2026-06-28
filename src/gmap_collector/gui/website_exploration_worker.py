from pathlib import Path

from PySide6.QtCore import QThread, Signal

from gmap_collector.browser.selenium_engine import SeleniumBrowserEngine
from gmap_collector.services.website_exploration_service import run_next_website_exploration_task
from gmap_collector.storage.website_exploration_repository import WebsiteExplorationRepository


class WebsiteExplorationWorker(QThread):
    """官网探索后台线程。

    官网请求可能较慢，必须放到 GUI 主线程之外执行。当前第一版按单线程顺序处理，
    每次只访问一个商家官网。
    """

    log_message = Signal(str)
    task_changed = Signal()
    finished_summary = Signal(object)

    def __init__(
        self,
        batch_id: int,
        database_path: Path,
        max_depth: int,
        max_pages: int,
        timeout_seconds: int = 15,
        browser_name: str = "chrome",
        selenium_cache_dir: Path | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.batch_id = batch_id
        self.database_path = Path(database_path)
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.timeout_seconds = timeout_seconds
        self.browser_name = browser_name
        self.selenium_cache_dir = Path(selenium_cache_dir) if selenium_cache_dir else None
        self.engine: SeleniumBrowserEngine | None = None
        self._stop_requested = False

    def run(self) -> None:
        """顺序执行官网探索任务。"""
        repository = WebsiteExplorationRepository(self.database_path)
        completed_count = 0
        failed_count = 0
        try:
            while not self._stop_requested:
                self.task_changed.emit()
                result = run_next_website_exploration_task(
                    repository=repository,
                    batch_id=self.batch_id,
                    max_depth=self.max_depth,
                    max_pages=self.max_pages,
                    timeout_seconds=self.timeout_seconds,
                    browser_fallback_fetch=self._fetch_with_browser,
                )
                if result is None:
                    break
                if result.succeeded:
                    completed_count += 1
                    fallback_text = "，已使用浏览器兜底" if result.used_browser_fallback else ""
                    self.log_message.emit(
                        f"官网探索完成：{result.business_name}，访问页面 {result.visited_count} 个{fallback_text}"
                    )
                else:
                    failed_count += 1
                    self.log_message.emit(f"官网探索失败：{result.business_name}，失败页面 {result.failed_count} 个")
                self.task_changed.emit()
        except Exception as error:
            self.log_message.emit(f"官网探索线程异常：{error}")
        finally:
            if self.engine is not None:
                self.engine.close()
                self.engine = None
            self.finished_summary.emit(
                {
                    "completed_count": completed_count,
                    "failed_count": failed_count,
                    "stopped_by_user": self._stop_requested,
                }
            )

    def request_stop(self) -> None:
        """请求在当前官网完成后停止。"""
        self._stop_requested = True

    def _fetch_with_browser(self, url: str, timeout_seconds: int) -> str:
        """使用 Selenium 打开官网并返回 HTML，作为静态请求失败后的兜底。"""
        if self.engine is None:
            self.engine = SeleniumBrowserEngine(
                browser_name=self.browser_name,
                page_load_timeout_seconds=timeout_seconds,
                cache_dir=(self.selenium_cache_dir / self.browser_name) if self.selenium_cache_dir else None,
            )
            self.engine.start()
        self.engine.open_url(url)
        self.engine.wait_for_page_ready(timeout_seconds)
        snapshot = self.engine.get_snapshot()
        return snapshot.html
