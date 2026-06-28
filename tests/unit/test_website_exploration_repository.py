from gmap_collector.common.models import BusinessRecord
from gmap_collector.storage.database import initialize_database
from gmap_collector.storage.repositories import BusinessRepository
from gmap_collector.storage.task_repository import KeywordTaskCreate, TaskRepository
from gmap_collector.storage.website_exploration_repository import WebsiteExplorationRepository
from gmap_collector.parsers.website_info_parser import WebsiteInfo


def test_create_exploration_batch_from_maps_task_creates_pending_and_skipped_tasks(tmp_path):
    """从 Google Maps 批次创建官网探索批次时，应按官网是否存在拆分待执行和跳过任务。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    maps_repository = TaskRepository(database_path)
    business_repository = BusinessRepository(database_path)
    exploration_repository = WebsiteExplorationRepository(database_path)

    maps_batch_id = maps_repository.create_batch(name="地图采集批次")
    maps_repository.add_keyword_tasks(maps_batch_id, [_keyword_task("Car Wrap Shop"), _keyword_task("PPF")])
    keyword_tasks = maps_repository.list_keyword_tasks(maps_batch_id)

    business_repository.upsert_business(
        _business_record(
            name="Alpha Wrap",
            website=" https://alpha.example.com ",
            google_maps_url="https://maps.google.com/?cid=1",
        ),
        keyword_task_id=keyword_tasks[0]["id"],
        query_text=keyword_tasks[0]["query_text"],
    )
    business_repository.upsert_business(
        _business_record(
            name="Beta Wrap",
            website="",
            google_maps_url="https://maps.google.com/?cid=2",
        ),
        keyword_task_id=keyword_tasks[0]["id"],
        query_text=keyword_tasks[0]["query_text"],
    )
    business_repository.upsert_business(
        _business_record(
            name="Alpha Wrap",
            website="https://alpha.example.com",
            google_maps_url="https://maps.google.com/?cid=1",
        ),
        keyword_task_id=keyword_tasks[1]["id"],
        query_text=keyword_tasks[1]["query_text"],
    )

    exploration_batch_id = exploration_repository.create_batch_from_maps_task(
        source_batch_id=maps_batch_id,
        runtime_config={"max_depth": 2},
    )

    batch = exploration_repository.get_batch(exploration_batch_id)
    tasks = exploration_repository.list_tasks(exploration_batch_id)

    assert batch["source_batch_id"] == maps_batch_id
    assert batch["runtime_config"]["max_depth"] == 2
    assert batch["total_businesses"] == 2
    assert batch["completed_businesses"] == 0
    assert batch["failed_businesses"] == 0
    assert batch["skipped_businesses"] == 1
    assert batch["status"] == "pending"
    assert [task["business_name"] for task in tasks] == ["Alpha Wrap", "Beta Wrap"]
    assert [task["status"] for task in tasks] == ["pending", "skipped"]
    assert tasks[0]["website_url"] == "https://alpha.example.com"
    assert tasks[1]["failure_reason"] == "无官网"


def test_exploration_repository_updates_task_status_and_batch_counts(tmp_path):
    """官网探索任务状态变化后，应能刷新批次完成、失败和跳过统计。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    maps_repository = TaskRepository(database_path)
    business_repository = BusinessRepository(database_path)
    exploration_repository = WebsiteExplorationRepository(database_path)

    maps_batch_id = maps_repository.create_batch(name="地图采集批次")
    maps_repository.add_keyword_tasks(maps_batch_id, [_keyword_task("Car Wrap Shop")])
    keyword_task = maps_repository.list_keyword_tasks(maps_batch_id)[0]
    business_repository.upsert_business(
        _business_record(
            name="Alpha Wrap",
            website="https://alpha.example.com",
            google_maps_url="https://maps.google.com/?cid=1",
        ),
        keyword_task_id=keyword_task["id"],
        query_text=keyword_task["query_text"],
    )
    business_repository.upsert_business(
        _business_record(
            name="Gamma Wrap",
            website="https://gamma.example.com",
            google_maps_url="https://maps.google.com/?cid=3",
        ),
        keyword_task_id=keyword_task["id"],
        query_text=keyword_task["query_text"],
    )

    exploration_batch_id = exploration_repository.create_batch_from_maps_task(source_batch_id=maps_batch_id)
    first_task = exploration_repository.get_next_pending_task(exploration_batch_id)
    assert first_task is not None

    exploration_repository.mark_task_running(first_task["id"])
    exploration_repository.mark_task_succeeded(first_task["id"])
    second_task = exploration_repository.get_next_pending_task(exploration_batch_id)
    assert second_task is not None
    exploration_repository.mark_task_failed(second_task["id"], "请求超时")
    exploration_repository.refresh_batch_counts(exploration_batch_id)

    batch = exploration_repository.get_batch(exploration_batch_id)
    tasks = exploration_repository.list_tasks(exploration_batch_id)

    assert batch["completed_businesses"] == 1
    assert batch["failed_businesses"] == 1
    assert batch["skipped_businesses"] == 0
    assert batch["status"] == "completed_with_errors"
    assert [task["status"] for task in tasks] == ["success", "failed"]
    assert tasks[1]["failure_reason"] == "请求超时"


def test_create_exploration_batch_from_empty_maps_task_completes_immediately(tmp_path):
    """来源批次没有命中商家时，官网探索批次应直接完成，避免界面出现永远待执行的空任务。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    maps_repository = TaskRepository(database_path)
    exploration_repository = WebsiteExplorationRepository(database_path)

    maps_batch_id = maps_repository.create_batch(name="空地图采集批次")
    exploration_batch_id = exploration_repository.create_batch_from_maps_task(source_batch_id=maps_batch_id)

    batch = exploration_repository.get_batch(exploration_batch_id)
    tasks = exploration_repository.list_tasks(exploration_batch_id)

    assert batch["total_businesses"] == 0
    assert batch["status"] == "completed"
    assert tasks == []


def test_exploration_repository_saves_result_to_business_and_marks_task_success(tmp_path):
    """官网探索结果应写回商家主表，并同步更新任务状态和批次统计。"""
    database_path = tmp_path / "app.sqlite3"
    initialize_database(database_path)
    maps_repository = TaskRepository(database_path)
    business_repository = BusinessRepository(database_path)
    exploration_repository = WebsiteExplorationRepository(database_path)

    maps_batch_id = maps_repository.create_batch(name="地图采集批次")
    maps_repository.add_keyword_tasks(maps_batch_id, [_keyword_task("Car Wrap Shop")])
    keyword_task = maps_repository.list_keyword_tasks(maps_batch_id)[0]
    business_repository.upsert_business(
        _business_record(
            name="Alpha Wrap",
            website="https://alpha.example.com",
            google_maps_url="https://maps.google.com/?cid=1",
        ),
        keyword_task_id=keyword_task["id"],
        query_text=keyword_task["query_text"],
    )
    exploration_batch_id = exploration_repository.create_batch_from_maps_task(source_batch_id=maps_batch_id)
    task = exploration_repository.get_next_pending_task(exploration_batch_id)
    assert task is not None

    exploration_repository.save_task_result(
        task_id=task["id"],
        info=WebsiteInfo(
            phones=["+49 30 1234 5678"],
            emails=["sales@example-wrap.de", "info@example-wrap.de"],
            instagram=["https://instagram.com/examplewrap"],
            tiktok=["https://tiktok.com/@examplewrap"],
            twitter_x=["https://x.com/examplewrap"],
            facebook=["https://facebook.com/examplewrap"],
            linkedin=["https://linkedin.com/company/examplewrap"],
            youtube=["https://youtube.com/@examplewrap"],
            whatsapp=["https://wa.me/493012345678"],
            seo_keywords=["car wrap", "ppf"],
        ),
    )

    business = business_repository.list_businesses()[0]
    updated_task = exploration_repository.list_tasks(exploration_batch_id)[0]
    batch = exploration_repository.get_batch(exploration_batch_id)

    assert business["explored_phone"] == "+49 30 1234 5678"
    assert business["emails"] == "sales@example-wrap.de,info@example-wrap.de"
    assert business["instagram"] == "https://instagram.com/examplewrap"
    assert business["tiktok"] == "https://tiktok.com/@examplewrap"
    assert business["twitter_x"] == "https://x.com/examplewrap"
    assert business["facebook"] == "https://facebook.com/examplewrap"
    assert business["linkedin"] == "https://linkedin.com/company/examplewrap"
    assert business["youtube"] == "https://youtube.com/@examplewrap"
    assert business["whatsapp"] == "https://wa.me/493012345678"
    assert business["seo_keywords"] == "car wrap,ppf"
    assert business["website_exploration_status"] == "已完成"
    assert business["website_explored_at"]
    assert updated_task["status"] == "success"
    assert batch["completed_businesses"] == 1
    assert batch["status"] == "completed"


def _keyword_task(keyword: str) -> KeywordTaskCreate:
    """构造关键词任务。"""
    return KeywordTaskCreate(
        keyword=keyword,
        country_name="德国",
        country_search_name="Germany",
        region_name="柏林州",
        region_search_name="Berlin",
        city_name="柏林",
        city_search_name="Berlin",
        query_text=f"{keyword} in Berlin, Berlin, Germany",
        search_url=f"https://www.google.com/maps/search/{keyword.replace(' ', '+')}+in+Berlin",
    )


def _business_record(name: str, website: str, google_maps_url: str) -> BusinessRecord:
    """构造商家记录。"""
    return BusinessRecord(
        name=name,
        address="Street 1",
        phone="+49 111",
        website=website,
        rating="4.8",
        review_count="120",
        category="Car wrap shop",
        google_maps_url=google_maps_url,
        source_keyword="Car Wrap Shop",
    )
