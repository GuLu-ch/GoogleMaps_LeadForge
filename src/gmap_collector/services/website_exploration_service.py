from dataclasses import dataclass

from gmap_collector.parsers.website_info_parser import WebsiteInfo, extract_website_info
from gmap_collector.services.website_crawler import WebsiteCrawlRequest, crawl_website
from gmap_collector.storage.website_exploration_repository import WebsiteExplorationRepository


@dataclass(frozen=True)
class WebsiteExplorationTaskResult:
    """单条官网探索任务执行结果。"""

    task_id: int
    business_name: str
    website_url: str
    visited_count: int
    failed_count: int
    succeeded: bool
    used_browser_fallback: bool = False


def run_next_website_exploration_task(
    repository: WebsiteExplorationRepository,
    batch_id: int,
    max_depth: int,
    max_pages: int,
    timeout_seconds: int = 15,
    fetch_html=None,
    browser_fallback_fetch=None,
) -> WebsiteExplorationTaskResult | None:
    """执行批次中的下一条官网探索任务。

    该函数只处理单条任务，方便 GUI Worker 后续用循环、暂停和停止控制任务节奏。
    """
    task = repository.get_next_pending_task(batch_id)
    if task is None:
        return None

    task_id = int(task["id"])
    website_url = str(task["website_url"])
    repository.mark_task_running(task_id)
    failed_reasons: list[str] = []
    crawl_result = None
    try:
        crawl_result = crawl_website(
            WebsiteCrawlRequest(
                start_url=website_url,
                max_depth=max_depth,
                max_pages=max_pages,
                timeout_seconds=timeout_seconds,
            ),
            fetch_html=fetch_html,
        )
    except Exception as error:
        failed_reasons.append(f"静态请求失败: {error}")

    if crawl_result is not None and crawl_result.failed_urls:
        failed_reasons.extend(f"{url}: {reason}" for url, reason in crawl_result.failed_urls.items())

    succeeded = False
    used_browser_fallback = False
    if crawl_result is not None and _has_core_info(crawl_result.info):
        repository.save_task_result(task_id, crawl_result.info)
        succeeded = True
    elif browser_fallback_fetch is not None:
        used_browser_fallback = True
        try:
            fallback_html = browser_fallback_fetch(website_url, timeout_seconds)
            fallback_info = extract_website_info(fallback_html, base_url=website_url)
        except Exception as error:
            failed_reasons.append(f"浏览器兜底失败: {error}")
            repository.mark_task_failed(task_id, _join_failure_reasons(failed_reasons))
        else:
            if _has_core_info(fallback_info):
                repository.save_task_result(task_id, fallback_info)
                succeeded = True
            else:
                failed_reasons.append("浏览器兜底未提取到核心联系方式")
                repository.mark_task_failed(task_id, _join_failure_reasons(failed_reasons))
    else:
        if crawl_result is None:
            failure_reason = _join_failure_reasons(failed_reasons)
        elif crawl_result.failed_urls and not crawl_result.visited_urls:
            failure_reason = _join_failure_reasons(failed_reasons)
        else:
            failure_reason = "未提取到核心联系方式"
            if failed_reasons:
                failure_reason = f"{failure_reason}; {_join_failure_reasons(failed_reasons)}"
        repository.mark_task_failed(task_id, failure_reason)

    return WebsiteExplorationTaskResult(
        task_id=task_id,
        business_name=str(task["business_name"]),
        website_url=website_url,
        visited_count=len(crawl_result.visited_urls) if crawl_result is not None else 0,
        failed_count=len(failed_reasons),
        succeeded=succeeded,
        used_browser_fallback=used_browser_fallback,
    )


def _has_core_info(info: WebsiteInfo) -> bool:
    """判断官网信息中是否包含核心联系方式。"""
    return bool(info.emails or info.phones or info.all_social_links())


def _join_failure_reasons(reasons: list[str]) -> str:
    """合并失败原因，保证写入数据库时不会为空。"""
    cleaned_reasons = [reason for reason in reasons if reason]
    return "; ".join(cleaned_reasons) if cleaned_reasons else "官网探索失败"
