from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from gmap_collector.services.maps_crawler import MapsCrawlResult, wait_random_seconds
from gmap_collector.storage.task_repository import TaskRepository


@dataclass(frozen=True)
class TaskRunConfig:
    """任务运行配置。"""

    consecutive_failure_pause_threshold: int
    keyword_wait_seconds_min: float = 0
    keyword_wait_seconds_max: float = 0


@dataclass(frozen=True)
class TaskRunSummary:
    """任务运行汇总。"""

    completed_count: int
    failed_count: int
    paused_by_user: bool
    stopped_by_user: bool
    paused_by_failure_threshold: bool


class TaskRunner:
    """顺序执行单个批次中的关键词任务。"""

    def __init__(
        self,
        task_repository: TaskRepository,
        crawl_one: Callable[[dict[str, Any]], MapsCrawlResult],
        config: TaskRunConfig,
        wait_between_keywords: Callable[[float, float], None] = wait_random_seconds,
    ):
        self.task_repository = task_repository
        self.crawl_one = crawl_one
        self.config = config
        self.wait_between_keywords = wait_between_keywords
        self._pause_requested = False
        self._stop_requested = False

    def request_pause(self) -> None:
        """请求在当前关键词完成后暂停。"""
        self._pause_requested = True

    def request_stop(self) -> None:
        """请求在当前关键词完成后停止。"""
        self._stop_requested = True

    def run_batch(self, batch_id: int) -> TaskRunSummary:
        """执行批次中所有待处理关键词。"""
        self._pause_requested = False
        self._stop_requested = False
        self.task_repository.reset_running_tasks_to_pending(batch_id)
        self.task_repository.mark_batch_running(batch_id)

        completed_count = 0
        failed_count = 0
        consecutive_failures = 0
        paused_by_failure_threshold = False

        while True:
            if self._pause_requested or self._stop_requested:
                break

            task = self.task_repository.get_next_pending_task(batch_id)
            if task is None:
                break

            self.task_repository.mark_task_running(task["id"])
            try:
                self.crawl_one(task)
            except Exception as error:
                failed_count += 1
                consecutive_failures += 1
                self.task_repository.mark_task_failed(task["id"], str(error))
            else:
                completed_count += 1
                consecutive_failures = 0
                self.task_repository.mark_task_succeeded(task["id"])

            if consecutive_failures >= self.config.consecutive_failure_pause_threshold:
                paused_by_failure_threshold = True
                break

            if self._pause_requested or self._stop_requested:
                break

            if self.task_repository.get_next_pending_task(batch_id) is not None:
                self._wait_before_next_keyword()

        if self._stop_requested:
            self.task_repository.refresh_batch_counts(batch_id)
            self.task_repository.mark_batch_stopped(batch_id)
        elif self._pause_requested or paused_by_failure_threshold:
            self.task_repository.refresh_batch_counts(batch_id)
            self.task_repository.mark_batch_paused(batch_id)
        else:
            self.task_repository.refresh_batch_counts(batch_id)

        return TaskRunSummary(
            completed_count=completed_count,
            failed_count=failed_count,
            paused_by_user=self._pause_requested,
            stopped_by_user=self._stop_requested,
            paused_by_failure_threshold=paused_by_failure_threshold,
        )

    def _wait_before_next_keyword(self) -> None:
        """在两个关键词之间按配置停留。"""
        maximum = max(0, self.config.keyword_wait_seconds_max)
        if maximum <= 0:
            return
        minimum = max(0, self.config.keyword_wait_seconds_min)
        self.wait_between_keywords(minimum, max(minimum, maximum))
