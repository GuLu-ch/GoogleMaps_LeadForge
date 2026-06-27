import time
from dataclasses import dataclass

from gmap_collector.browser.base import BrowserEngine
from gmap_collector.parsers.maps_list_parser import parse_maps_list_results
from gmap_collector.storage.repositories import BusinessRepository


@dataclass(frozen=True)
class MapsCrawlRequest:
    """单个 Google Maps 搜索链接采集请求。"""

    search_url: str
    source_keyword: str
    max_scroll_rounds: int
    no_new_results_threshold: int
    scroll_wait_seconds: float


@dataclass(frozen=True)
class MapsCrawlResult:
    """单个搜索链接采集结果。"""

    parsed_count: int
    saved_count: int
    final_url: str


def crawl_maps_search(
    engine: BrowserEngine,
    repository: BusinessRepository,
    request: MapsCrawlRequest,
) -> MapsCrawlResult:
    """采集一个 Google Maps 搜索结果列表并写入 SQLite。

    该函数只处理“列表页滚动 + 当前 DOM 解析 + 去重保存”的核心闭环。
    浏览器启动、关闭、失败重试和任务状态更新由上层调度器负责。
    """
    engine.open_url(request.search_url)

    records = []
    previous_count = -1
    no_new_results_rounds = 0
    final_url = request.search_url

    for _ in range(request.max_scroll_rounds):
        snapshot = engine.get_snapshot()
        final_url = snapshot.current_url or final_url
        records = parse_maps_list_results(snapshot.html, source_keyword=request.source_keyword)

        if len(records) == previous_count:
            no_new_results_rounds += 1
        else:
            no_new_results_rounds = 0
            previous_count = len(records)

        if no_new_results_rounds >= request.no_new_results_threshold or engine.is_at_results_bottom():
            break

        engine.scroll_results()
        if request.scroll_wait_seconds > 0:
            time.sleep(request.scroll_wait_seconds)

    saved_count = 0
    for record in records:
        repository.upsert_business(record)
        saved_count += 1

    return MapsCrawlResult(
        parsed_count=len(records),
        saved_count=saved_count,
        final_url=final_url,
    )
