from pathlib import Path

from PySide6.QtCore import QThread, Signal

from gmap_collector.browser.selenium_engine import SeleniumBrowserEngine
from gmap_collector.services.maps_crawler import MapsCrawlRequest, crawl_maps_search
from gmap_collector.services.task_runner import TaskRunConfig, TaskRunSummary, TaskRunner
from gmap_collector.storage.repositories import BusinessRepository
from gmap_collector.storage.task_repository import TaskRepository


class TaskWorker(QThread):
    """任务执行线程。

    浏览器自动化必须放在 GUI 主线程之外，避免界面卡死。暂停和停止请求会在当前关键词
    执行结束后生效，避免强行中断浏览器导致状态不一致。
    """

    log_message = Signal(str)
    task_changed = Signal()
    finished_summary = Signal(object)

    def __init__(
        self,
        batch_id: int,
        database_path: Path,
        browser_name: str,
        page_load_timeout_seconds: int,
        page_initial_wait_seconds: float,
        max_scroll_rounds: int,
        no_new_results_threshold: int,
        scroll_wait_seconds_min: float,
        scroll_wait_seconds_max: float,
        keyword_wait_seconds_min: float,
        keyword_wait_seconds_max: float,
        failure_threshold: int,
        selenium_cache_dir: Path,
        parent=None,
    ):
        super().__init__(parent)
        self.batch_id = batch_id
        self.database_path = database_path
        self.browser_name = browser_name
        self.page_load_timeout_seconds = page_load_timeout_seconds
        self.page_initial_wait_seconds = page_initial_wait_seconds
        self.max_scroll_rounds = max_scroll_rounds
        self.no_new_results_threshold = no_new_results_threshold
        self.scroll_wait_seconds_min = scroll_wait_seconds_min
        self.scroll_wait_seconds_max = scroll_wait_seconds_max
        self.keyword_wait_seconds_min = keyword_wait_seconds_min
        self.keyword_wait_seconds_max = keyword_wait_seconds_max
        self.failure_threshold = failure_threshold
        self.selenium_cache_dir = selenium_cache_dir
        self.runner: TaskRunner | None = None
        self.engine: SeleniumBrowserEngine | None = None

    def run(self) -> None:
        """执行任务批次。"""
        task_repository = TaskRepository(self.database_path)
        business_repository = BusinessRepository(self.database_path)
        self.engine = SeleniumBrowserEngine(
            browser_name=self.browser_name,
            page_load_timeout_seconds=self.page_load_timeout_seconds,
            cache_dir=self.selenium_cache_dir / self.browser_name,
        )

        def crawl_one(task: dict):
            self.task_changed.emit()
            self.log_message.emit(f"开始采集：{task['query_text']}")
            result = crawl_maps_search(
                engine=self.engine,
                repository=business_repository,
                request=MapsCrawlRequest(
                    search_url=task["search_url"],
                    source_keyword=task["keyword"],
                    max_scroll_rounds=self.max_scroll_rounds,
                    no_new_results_threshold=self.no_new_results_threshold,
                    scroll_wait_seconds_min=self.scroll_wait_seconds_min,
                    scroll_wait_seconds_max=self.scroll_wait_seconds_max,
                    page_initial_wait_seconds=self.page_initial_wait_seconds,
                    keyword_task_id=task["id"],
                    query_text=task["query_text"],
                ),
            )
            self.log_message.emit(f"完成采集：解析 {result.parsed_count} 条，写入 {result.saved_count} 条")
            self.task_changed.emit()
            return result

        summary = TaskRunSummary(0, 0, False, False, False)
        try:
            self.engine.start()
            self.runner = TaskRunner(
                task_repository=task_repository,
                crawl_one=crawl_one,
                config=TaskRunConfig(
                    consecutive_failure_pause_threshold=self.failure_threshold,
                    keyword_wait_seconds_min=self.keyword_wait_seconds_min,
                    keyword_wait_seconds_max=self.keyword_wait_seconds_max,
                ),
            )
            summary = self.runner.run_batch(self.batch_id)
        except Exception as error:
            self.log_message.emit(f"任务执行异常：{error}")
        finally:
            if self.engine is not None:
                self.engine.close()
            self.finished_summary.emit(summary)

    def request_pause(self) -> None:
        """请求暂停。"""
        if self.runner is not None:
            self.runner.request_pause()

    def request_stop(self) -> None:
        """请求停止。"""
        if self.runner is not None:
            self.runner.request_stop()
