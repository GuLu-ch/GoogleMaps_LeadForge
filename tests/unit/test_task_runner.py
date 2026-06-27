from gmap_collector.services.maps_crawler import MapsCrawlResult
from gmap_collector.services.task_runner import TaskRunConfig, TaskRunner
from gmap_collector.storage.database import initialize_database
from gmap_collector.storage.task_repository import KeywordTaskCreate, TaskRepository


def _task(keyword: str) -> KeywordTaskCreate:
    """创建测试关键词任务。"""
    return KeywordTaskCreate(
        keyword=keyword,
        country_name="德国",
        country_search_name="Germany",
        region_name="柏林州",
        region_search_name="Berlin",
        city_name="柏林",
        city_search_name="Berlin",
        query_text=f"{keyword} in Berlin, Berlin, Germany",
        search_url=f"https://www.google.com/maps/search/{keyword}",
    )


def test_task_runner_processes_pending_tasks_and_updates_status(tmp_path):
    """任务运行器应按顺序执行待处理关键词并刷新批次统计。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    repository = TaskRepository(database_path)
    batch_id = repository.create_batch("测试批次")
    repository.add_keyword_tasks(batch_id, [_task("Car Wrap Shop"), _task("PPF")])
    called_keywords: list[str] = []

    def fake_crawl(task):
        called_keywords.append(task["keyword"])
        return MapsCrawlResult(parsed_count=1, saved_count=1, final_url=task["search_url"])

    runner = TaskRunner(
        task_repository=repository,
        crawl_one=fake_crawl,
        config=TaskRunConfig(consecutive_failure_pause_threshold=3),
    )

    summary = runner.run_batch(batch_id)

    batch = repository.get_batch(batch_id)
    tasks = repository.list_keyword_tasks(batch_id)
    assert summary.completed_count == 2
    assert summary.failed_count == 0
    assert called_keywords == ["Car Wrap Shop", "PPF"]
    assert batch["status"] == "completed"
    assert [task["status"] for task in tasks] == ["success", "success"]


def test_task_runner_waits_between_keywords(tmp_path):
    """任务运行器应在关键词之间执行配置的停留函数，最后一个关键词后不再停留。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    repository = TaskRepository(database_path)
    batch_id = repository.create_batch("测试批次")
    repository.add_keyword_tasks(batch_id, [_task("A"), _task("B")])
    wait_calls: list[tuple[float, float]] = []

    def fake_crawl(task):
        return MapsCrawlResult(parsed_count=1, saved_count=1, final_url=task["search_url"])

    runner = TaskRunner(
        task_repository=repository,
        crawl_one=fake_crawl,
        config=TaskRunConfig(
            consecutive_failure_pause_threshold=3,
            keyword_wait_seconds_min=8,
            keyword_wait_seconds_max=15,
        ),
        wait_between_keywords=lambda minimum, maximum: wait_calls.append((minimum, maximum)),
    )

    runner.run_batch(batch_id)

    assert wait_calls == [(8, 15)]


def test_task_runner_does_not_wait_between_keywords_after_pause_request(tmp_path):
    """请求暂停后，运行器不应再执行关键词间停留。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    repository = TaskRepository(database_path)
    batch_id = repository.create_batch("测试批次")
    repository.add_keyword_tasks(batch_id, [_task("A"), _task("B")])
    wait_calls: list[tuple[float, float]] = []
    runner: TaskRunner

    def fake_crawl(task):
        runner.request_pause()
        return MapsCrawlResult(parsed_count=1, saved_count=1, final_url=task["search_url"])

    runner = TaskRunner(
        task_repository=repository,
        crawl_one=fake_crawl,
        config=TaskRunConfig(
            consecutive_failure_pause_threshold=3,
            keyword_wait_seconds_min=8,
            keyword_wait_seconds_max=15,
        ),
        wait_between_keywords=lambda minimum, maximum: wait_calls.append((minimum, maximum)),
    )

    summary = runner.run_batch(batch_id)

    assert summary.paused_by_user is True
    assert wait_calls == []


def test_task_runner_pauses_after_consecutive_failures(tmp_path):
    """连续失败达到阈值时，运行器应暂停批次并保留后续待执行任务。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    repository = TaskRepository(database_path)
    batch_id = repository.create_batch("测试批次")
    repository.add_keyword_tasks(batch_id, [_task("A"), _task("B"), _task("C")])

    def fake_crawl(task):
        raise RuntimeError(f"{task['keyword']} 失败")

    runner = TaskRunner(
        task_repository=repository,
        crawl_one=fake_crawl,
        config=TaskRunConfig(consecutive_failure_pause_threshold=2),
    )

    summary = runner.run_batch(batch_id)

    batch = repository.get_batch(batch_id)
    tasks = repository.list_keyword_tasks(batch_id)
    assert summary.completed_count == 0
    assert summary.failed_count == 2
    assert summary.paused_by_failure_threshold is True
    assert batch["status"] == "paused"
    assert batch["failed_keywords"] == 2
    assert [task["status"] for task in tasks] == ["failed", "failed", "pending"]
