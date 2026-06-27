from gmap_collector.storage.database import initialize_database
from gmap_collector.storage.task_repository import KeywordTaskCreate, TaskRepository


def test_task_repository_creates_batch_and_tracks_keyword_status(tmp_path):
    """任务仓储应能创建批次、插入关键词任务并更新执行状态。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    repository = TaskRepository(database_path)

    batch_id = repository.create_batch(name="测试批次")
    repository.add_keyword_tasks(
        batch_id,
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
            ),
            KeywordTaskCreate(
                keyword="PPF",
                country_name="德国",
                country_search_name="Germany",
                region_name="柏林州",
                region_search_name="Berlin",
                city_name="柏林",
                city_search_name="Berlin",
                query_text="PPF in Berlin, Berlin, Germany",
                search_url="https://www.google.com/maps/search/PPF+in+Berlin",
            ),
        ],
    )

    batch = repository.get_batch(batch_id)
    first_task = repository.get_next_pending_task(batch_id)

    assert batch["status"] == "pending"
    assert batch["total_keywords"] == 2
    assert first_task is not None
    assert first_task["keyword"] == "Car Wrap Shop"

    repository.mark_task_running(first_task["id"])
    repository.mark_task_succeeded(first_task["id"])
    second_task = repository.get_next_pending_task(batch_id)
    assert second_task is not None
    repository.mark_task_failed(second_task["id"], "页面加载失败")
    repository.refresh_batch_counts(batch_id)

    updated_batch = repository.get_batch(batch_id)
    tasks = repository.list_keyword_tasks(batch_id)

    assert updated_batch["completed_keywords"] == 1
    assert updated_batch["failed_keywords"] == 1
    assert updated_batch["status"] == "completed_with_errors"
    assert [task["status"] for task in tasks] == ["success", "failed"]
    assert tasks[1]["failure_reason"] == "页面加载失败"


def test_task_repository_resets_failed_tasks_for_retry(tmp_path):
    """重试失败关键词时，应只把失败任务还原为待执行并清空失败原因。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    repository = TaskRepository(database_path)
    batch_id = repository.create_batch(name="测试批次")
    repository.add_keyword_tasks(
        batch_id,
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
            ),
            KeywordTaskCreate(
                keyword="PPF",
                country_name="德国",
                country_search_name="Germany",
                region_name="柏林州",
                region_search_name="Berlin",
                city_name="柏林",
                city_search_name="Berlin",
                query_text="PPF in Berlin, Berlin, Germany",
                search_url="https://www.google.com/maps/search/PPF+in+Berlin",
            ),
        ],
    )
    tasks = repository.list_keyword_tasks(batch_id)
    repository.mark_task_succeeded(tasks[0]["id"])
    repository.mark_task_failed(tasks[1]["id"], "页面加载失败")
    repository.refresh_batch_counts(batch_id)

    reset_count = repository.reset_failed_tasks_to_pending(batch_id)
    repository.refresh_batch_counts(batch_id)

    batch = repository.get_batch(batch_id)
    tasks = repository.list_keyword_tasks(batch_id)
    assert reset_count == 1
    assert batch["completed_keywords"] == 1
    assert batch["failed_keywords"] == 0
    assert batch["status"] == "pending"
    assert [task["status"] for task in tasks] == ["success", "pending"]
    assert tasks[1]["failure_reason"] == ""


def test_task_repository_finds_latest_resumable_batch(tmp_path):
    """应用启动时应能找到最近一个仍可继续处理的批次。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    repository = TaskRepository(database_path)

    stopped_batch_id = repository.create_batch(name="已停止批次")
    pending_batch_id = repository.create_batch(name="可恢复批次")
    repository.mark_batch_stopped(stopped_batch_id)

    assert repository.get_latest_resumable_batch_id() == pending_batch_id


def test_task_repository_persists_batch_runtime_config_snapshot(tmp_path):
    """创建批次时应保存本次任务运行参数快照，便于暂停和重启后恢复。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    repository = TaskRepository(database_path)

    batch_id = repository.create_batch(
        name="带运行参数的批次",
        runtime_config={
            "browser_name": "chrome",
            "max_scroll_rounds": 8,
            "scroll_wait_seconds_min": 2,
            "scroll_wait_seconds_max": 5,
        },
    )

    batch = repository.get_batch(batch_id)

    assert batch["runtime_config"]["browser_name"] == "chrome"
    assert batch["runtime_config"]["max_scroll_rounds"] == 8
    assert batch["runtime_config"]["scroll_wait_seconds_min"] == 2
    assert batch["runtime_config"]["scroll_wait_seconds_max"] == 5
