from gmap_collector.common.models import BusinessRecord
from gmap_collector.storage.database import initialize_database
from gmap_collector.storage.repositories import BusinessRepository
from gmap_collector.storage.task_repository import KeywordTaskCreate, TaskRepository
from gmap_collector.storage.website_exploration_repository import WebsiteExplorationRepository
from gmap_collector.services.website_exploration_service import run_next_website_exploration_task


def test_run_next_website_exploration_task_crawls_and_saves_result(tmp_path):
    """执行一条官网探索任务时，应抓取官网、写回结果并更新任务状态。"""
    database_path, exploration_batch_id = _prepare_exploration_database(tmp_path)
    repository = WebsiteExplorationRepository(database_path)
    pages = {
        "https://alpha.example.com/": """
            <html>
              <head><meta name="keywords" content="wrap, ppf"></head>
              <body>
                <p>sales@example-wrap.de</p>
                <p>+49 30 1234 5678</p>
                <a href="https://www.instagram.com/examplewrap">Instagram</a>
              </body>
            </html>
        """
    }

    result = run_next_website_exploration_task(
        repository=repository,
        batch_id=exploration_batch_id,
        max_depth=1,
        max_pages=5,
        fetch_html=lambda url: pages[url],
    )

    businesses = BusinessRepository(database_path).list_businesses()
    tasks = repository.list_tasks(exploration_batch_id)

    assert result is not None
    assert result.business_name == "Alpha Wrap"
    assert result.visited_count == 1
    assert result.failed_count == 0
    assert businesses[0]["emails"] == "sales@example-wrap.de"
    assert businesses[0]["explored_phone"] == "+49 30 1234 5678"
    assert businesses[0]["instagram"] == "https://www.instagram.com/examplewrap"
    assert businesses[0]["seo_keywords"] == "wrap,ppf"
    assert tasks[0]["status"] == "success"


def test_run_next_website_exploration_task_marks_failure_when_crawl_fails(tmp_path):
    """官网抓取失败时，应把当前探索任务标记为失败并记录原因。"""
    database_path, exploration_batch_id = _prepare_exploration_database(tmp_path)
    repository = WebsiteExplorationRepository(database_path)

    result = run_next_website_exploration_task(
        repository=repository,
        batch_id=exploration_batch_id,
        max_depth=1,
        max_pages=5,
        fetch_html=lambda url: (_ for _ in ()).throw(TimeoutError("请求超时")),
    )

    tasks = repository.list_tasks(exploration_batch_id)
    batch = repository.get_batch(exploration_batch_id)

    assert result is not None
    assert result.failed_count == 1
    assert tasks[0]["status"] == "failed"
    assert "请求超时" in tasks[0]["failure_reason"]
    assert batch["failed_businesses"] == 1


def test_run_next_website_exploration_task_uses_browser_fallback_when_static_has_no_core_info(tmp_path):
    """静态请求未提取到核心联系方式时，应尝试浏览器兜底并保存兜底结果。"""
    database_path, exploration_batch_id = _prepare_exploration_database(tmp_path)
    repository = WebsiteExplorationRepository(database_path)
    fallback_calls = []

    def fake_browser_fallback(url: str, timeout_seconds: int) -> str:
        fallback_calls.append((url, timeout_seconds))
        return """
            <html>
              <body>
                <p>fallback@example-wrap.de</p>
                <a href="https://www.linkedin.com/company/fallback-wrap">LinkedIn</a>
              </body>
            </html>
        """

    result = run_next_website_exploration_task(
        repository=repository,
        batch_id=exploration_batch_id,
        max_depth=1,
        max_pages=5,
        timeout_seconds=7,
        fetch_html=lambda url, timeout_seconds: "<html><body>No contact yet</body></html>",
        browser_fallback_fetch=fake_browser_fallback,
    )

    businesses = BusinessRepository(database_path).list_businesses()
    tasks = repository.list_tasks(exploration_batch_id)

    assert result is not None
    assert fallback_calls == [("https://alpha.example.com", 7)]
    assert businesses[0]["emails"] == "fallback@example-wrap.de"
    assert businesses[0]["linkedin"] == "https://www.linkedin.com/company/fallback-wrap"
    assert tasks[0]["status"] == "success"


def test_run_next_website_exploration_task_reports_success_when_fallback_recovers_static_failure(tmp_path):
    """静态请求失败但浏览器兜底成功时，结果应按成功统计。"""
    database_path, exploration_batch_id = _prepare_exploration_database(tmp_path)
    repository = WebsiteExplorationRepository(database_path)

    result = run_next_website_exploration_task(
        repository=repository,
        batch_id=exploration_batch_id,
        max_depth=1,
        max_pages=5,
        timeout_seconds=5,
        fetch_html=lambda url, timeout_seconds: (_ for _ in ()).throw(TimeoutError("静态请求超时")),
        browser_fallback_fetch=lambda url, timeout_seconds: "<html><body>fallback@example-wrap.de</body></html>",
    )

    businesses = BusinessRepository(database_path).list_businesses()
    tasks = repository.list_tasks(exploration_batch_id)

    assert result is not None
    assert result.succeeded is True
    assert result.used_browser_fallback is True
    assert result.failed_count == 1
    assert businesses[0]["emails"] == "fallback@example-wrap.de"
    assert tasks[0]["status"] == "success"


def test_run_next_website_exploration_task_marks_failure_when_static_and_fallback_fail(tmp_path):
    """静态请求和浏览器兜底都失败时，应标记失败并释放 running 状态。"""
    database_path, exploration_batch_id = _prepare_exploration_database(tmp_path)
    repository = WebsiteExplorationRepository(database_path)

    result = run_next_website_exploration_task(
        repository=repository,
        batch_id=exploration_batch_id,
        max_depth=1,
        max_pages=5,
        timeout_seconds=3,
        fetch_html=lambda url, timeout_seconds: (_ for _ in ()).throw(TimeoutError("静态请求超时")),
        browser_fallback_fetch=lambda url, timeout_seconds: (_ for _ in ()).throw(RuntimeError("浏览器兜底失败")),
    )

    tasks = repository.list_tasks(exploration_batch_id)
    batch = repository.get_batch(exploration_batch_id)

    assert result is not None
    assert result.failed_count == 2
    assert tasks[0]["status"] == "failed"
    assert "静态请求超时" in tasks[0]["failure_reason"]
    assert "浏览器兜底失败" in tasks[0]["failure_reason"]
    assert batch["failed_businesses"] == 1


def test_run_next_website_exploration_task_returns_none_when_no_pending_task(tmp_path):
    """没有待执行官网任务时，应返回 None。"""
    database_path, exploration_batch_id = _prepare_exploration_database(tmp_path)
    repository = WebsiteExplorationRepository(database_path)
    task = repository.get_next_pending_task(exploration_batch_id)
    assert task is not None
    repository.mark_task_skipped(task["id"], "手动跳过")

    result = run_next_website_exploration_task(
        repository=repository,
        batch_id=exploration_batch_id,
        max_depth=1,
        max_pages=5,
        fetch_html=lambda url: "",
    )

    assert result is None


def _prepare_exploration_database(tmp_path):
    """准备包含一条有官网商家的官网探索批次。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    maps_repository = TaskRepository(database_path)
    business_repository = BusinessRepository(database_path)
    exploration_repository = WebsiteExplorationRepository(database_path)

    maps_batch_id = maps_repository.create_batch(name="地图采集批次")
    maps_repository.add_keyword_tasks(
        maps_batch_id,
        [
            KeywordTaskCreate(
                keyword="Car Wrap Shop",
                country_name="德国",
                country_search_name="Germany",
                region_name="柏林州",
                region_search_name="Berlin",
                city_name="柏林",
                city_search_name="Berlin",
                query_text="Car Wrap Shop in Berlin, Berlin, Germany",
                search_url="https://www.google.com/maps/search/Car+Wrap+Shop+in+Berlin",
            )
        ],
    )
    keyword_task = maps_repository.list_keyword_tasks(maps_batch_id)[0]
    business_repository.upsert_business(
        BusinessRecord(
            name="Alpha Wrap",
            address="Street 1",
            phone="+49 111",
            website="https://alpha.example.com",
            rating="4.8",
            review_count="120",
            category="Car wrap shop",
            google_maps_url="https://maps.google.com/?cid=1",
            source_keyword="Car Wrap Shop",
        ),
        keyword_task_id=keyword_task["id"],
        query_text=keyword_task["query_text"],
    )
    exploration_batch_id = exploration_repository.create_batch_from_maps_task(source_batch_id=maps_batch_id)
    return database_path, exploration_batch_id
