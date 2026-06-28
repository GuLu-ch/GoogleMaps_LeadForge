import json
import sqlite3
from pathlib import Path
from typing import Any

from gmap_collector.parsers.website_info_parser import WebsiteInfo


class WebsiteExplorationRepository:
    """官网探索任务仓储。

    该仓储只负责二次采集任务的创建、状态流转和统计刷新，不直接访问网站。
    后续真正的官网抓取器只需要从这里领取待执行任务并回写结果。
    """

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def create_batch_from_maps_task(
        self,
        source_batch_id: int,
        runtime_config: dict[str, Any] | None = None,
        name: str | None = None,
    ) -> int:
        """从 Google Maps 批次命中的去重商家创建官网探索批次。

        同一个商家即使被来源批次中的多个关键词命中，也只创建一条官网探索任务。
        有官网的商家进入待执行状态；没有官网的商家直接标记为跳过，并写入原因。
        """
        with self._connect() as connection:
            self._ensure_source_batch_exists(connection, source_batch_id)
            batch_name = name or f"官网探索批次 - 来源任务 {source_batch_id}"
            cursor = connection.execute(
                """
                INSERT INTO website_exploration_batches (source_batch_id, name, status, runtime_config)
                VALUES (?, ?, 'pending', ?)
                """,
                (source_batch_id, batch_name, json.dumps(runtime_config or {}, ensure_ascii=False)),
            )
            exploration_batch_id = int(cursor.lastrowid)
            businesses = self._list_source_businesses(connection, source_batch_id)
            for business in businesses:
                website_url = str(business["website"] or "").strip()
                if website_url:
                    status = "pending"
                    failure_reason = ""
                else:
                    status = "skipped"
                    failure_reason = "无官网"
                connection.execute(
                    """
                    INSERT INTO website_exploration_tasks (
                        batch_id, business_id, business_name, website_url, status, failure_reason
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        exploration_batch_id,
                        int(business["id"]),
                        str(business["name"] or ""),
                        website_url,
                        status,
                        failure_reason,
                    ),
                )
            self._refresh_batch_counts(connection, exploration_batch_id)
            connection.commit()
            return exploration_batch_id

    def get_batch(self, batch_id: int) -> dict[str, Any]:
        """读取官网探索批次。"""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM website_exploration_batches WHERE id = ?",
                (batch_id,),
            ).fetchone()
        if row is None:
            raise ValueError(f"官网探索批次不存在: {batch_id}")
        batch = dict(row)
        batch["runtime_config"] = _load_runtime_config(batch.get("runtime_config", "{}"))
        return batch

    def list_batches(self) -> list[dict[str, Any]]:
        """按创建时间倒序返回官网探索批次。"""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM website_exploration_batches
                ORDER BY id DESC
                """
            ).fetchall()
        batches = [dict(row) for row in rows]
        for batch in batches:
            batch["runtime_config"] = _load_runtime_config(batch.get("runtime_config", "{}"))
        return batches

    def list_tasks(self, batch_id: int) -> list[dict[str, Any]]:
        """按创建顺序返回官网探索任务。"""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM website_exploration_tasks
                WHERE batch_id = ?
                ORDER BY id
                """,
                (batch_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_next_pending_task(self, batch_id: int) -> dict[str, Any] | None:
        """返回批次中下一条待执行的官网探索任务。"""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM website_exploration_tasks
                WHERE batch_id = ? AND status = 'pending'
                ORDER BY id
                LIMIT 1
                """,
                (batch_id,),
            ).fetchone()
        return dict(row) if row else None

    def mark_task_running(self, task_id: int) -> None:
        """标记官网探索任务运行中。"""
        self._update_task_status(task_id, "running", "")

    def mark_task_succeeded(self, task_id: int) -> None:
        """标记官网探索任务成功。"""
        self._update_task_status(task_id, "success", "")

    def mark_task_failed(self, task_id: int, failure_reason: str) -> None:
        """标记官网探索任务失败。"""
        self._update_task_status(task_id, "failed", failure_reason)

    def mark_task_skipped(self, task_id: int, failure_reason: str) -> None:
        """标记官网探索任务跳过。"""
        self._update_task_status(task_id, "skipped", failure_reason)

    def save_task_result(self, task_id: int, info: WebsiteInfo) -> None:
        """保存官网探索结果并标记任务成功。

        官网探索结果最终汇总到商家主表，结果管理页和导出都从商家主表读取。
        多值字段按英文逗号合并，便于 CSV/Excel 直接展示。
        """
        with self._connect() as connection:
            task = connection.execute(
                "SELECT * FROM website_exploration_tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
            if task is None:
                raise ValueError(f"官网探索任务不存在: {task_id}")

            connection.execute(
                """
                UPDATE businesses
                SET explored_phone = ?,
                    emails = ?,
                    instagram = ?,
                    tiktok = ?,
                    twitter_x = ?,
                    facebook = ?,
                    linkedin = ?,
                    youtube = ?,
                    whatsapp = ?,
                    seo_keywords = ?,
                    website_exploration_status = '已完成',
                    website_explored_at = CURRENT_TIMESTAMP,
                    last_seen_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    _join_values(info.phones),
                    _join_values(info.emails),
                    _join_values(info.instagram),
                    _join_values(info.tiktok),
                    _join_values(info.twitter_x),
                    _join_values(info.facebook),
                    _join_values(info.linkedin),
                    _join_values(info.youtube),
                    _join_values(info.whatsapp),
                    _join_values(info.seo_keywords),
                    int(task["business_id"]),
                ),
            )
            connection.execute(
                """
                UPDATE website_exploration_tasks
                SET status = 'success',
                    failure_reason = '',
                    last_run_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (task_id,),
            )
            self._refresh_batch_counts(connection, int(task["batch_id"]))
            connection.commit()

    def refresh_batch_counts(self, batch_id: int) -> None:
        """刷新官网探索批次统计。"""
        with self._connect() as connection:
            self._refresh_batch_counts(connection, batch_id)
            connection.commit()

    def _ensure_source_batch_exists(self, connection: sqlite3.Connection, source_batch_id: int) -> None:
        """确认来源 Google Maps 批次存在，避免生成孤立探索任务。"""
        row = connection.execute("SELECT id FROM task_batches WHERE id = ?", (source_batch_id,)).fetchone()
        if row is None:
            raise ValueError(f"来源 Google Maps 批次不存在: {source_batch_id}")

    def _list_source_businesses(self, connection: sqlite3.Connection, source_batch_id: int) -> list[sqlite3.Row]:
        """读取来源批次命中的去重商家。

        来源批次可能通过多个关键词命中同一商家，因此这里按商家主表 ID 去重。
        """
        return connection.execute(
            """
            SELECT DISTINCT
                businesses.id,
                businesses.name,
                businesses.website
            FROM businesses
            INNER JOIN business_task_hits ON business_task_hits.business_id = businesses.id
            INNER JOIN keyword_tasks ON keyword_tasks.id = business_task_hits.keyword_task_id
            WHERE keyword_tasks.batch_id = ?
            ORDER BY businesses.id
            """,
            (source_batch_id,),
        ).fetchall()

    def _refresh_batch_counts(self, connection: sqlite3.Connection, batch_id: int) -> None:
        """根据任务状态刷新批次统计和批次最终状态。"""
        counts = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) AS skipped_count,
                SUM(CASE WHEN status IN ('pending', 'running') THEN 1 ELSE 0 END) AS remaining_count
            FROM website_exploration_tasks
            WHERE batch_id = ?
            """,
            (batch_id,),
        ).fetchone()

        total = int(counts["total"] or 0)
        success_count = int(counts["success_count"] or 0)
        failed_count = int(counts["failed_count"] or 0)
        skipped_count = int(counts["skipped_count"] or 0)
        remaining_count = int(counts["remaining_count"] or 0)
        if remaining_count > 0:
            status = "pending"
        elif failed_count > 0:
            status = "completed_with_errors"
        else:
            status = "completed"

        connection.execute(
            """
            UPDATE website_exploration_batches
            SET total_businesses = ?,
                completed_businesses = ?,
                failed_businesses = ?,
                skipped_businesses = ?,
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (total, success_count, failed_count, skipped_count, status, batch_id),
        )

    def _update_task_status(self, task_id: int, status: str, failure_reason: str) -> None:
        """更新官网探索任务状态。"""
        with self._connect() as connection:
            task = connection.execute(
                "SELECT batch_id FROM website_exploration_tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
            if task is None:
                raise ValueError(f"官网探索任务不存在: {task_id}")
            connection.execute(
                """
                UPDATE website_exploration_tasks
                SET status = ?,
                    failure_reason = ?,
                    last_run_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, failure_reason, task_id),
            )
            self._refresh_batch_counts(connection, int(task["batch_id"]))
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        """创建 SQLite 连接。"""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


def _load_runtime_config(value: str) -> dict[str, Any]:
    """从数据库字段读取官网探索运行参数快照。"""
    try:
        loaded = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _join_values(values: list[str]) -> str:
    """将多值字段合并为英文逗号分隔字符串。"""
    return ",".join(value.strip() for value in values if value.strip())
