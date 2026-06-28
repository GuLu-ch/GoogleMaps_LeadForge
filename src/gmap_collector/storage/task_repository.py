import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class KeywordTaskCreate:
    """创建关键词任务需要的字段。"""

    keyword: str
    country_name: str
    country_search_name: str
    region_name: str
    region_search_name: str
    city_name: str
    city_search_name: str
    query_text: str
    search_url: str


class TaskRepository:
    """任务批次和关键词任务仓储。"""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def create_batch(self, name: str, runtime_config: dict[str, Any] | None = None) -> int:
        """创建任务批次并返回批次 ID。"""
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO task_batches (name, status, total_keywords, runtime_config)
                VALUES (?, 'pending', 0, ?)
                """,
                (name, json.dumps(runtime_config or {}, ensure_ascii=False)),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def add_keyword_tasks(self, batch_id: int, tasks: list[KeywordTaskCreate]) -> None:
        """批量添加关键词任务。"""
        if not tasks:
            return

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO keyword_tasks (
                    batch_id, keyword, country_name, country_search_name,
                    region_name, region_search_name, city_name, city_search_name,
                    query_text, search_url, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """,
                [
                    (
                        batch_id,
                        task.keyword,
                        task.country_name,
                        task.country_search_name,
                        task.region_name,
                        task.region_search_name,
                        task.city_name,
                        task.city_search_name,
                        task.query_text,
                        task.search_url,
                    )
                    for task in tasks
                ],
            )
            connection.execute(
                """
                UPDATE task_batches
                SET total_keywords = (
                        SELECT COUNT(*) FROM keyword_tasks WHERE batch_id = ?
                    ),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (batch_id, batch_id),
            )
            connection.commit()

    def get_batch(self, batch_id: int) -> dict[str, Any]:
        """读取任务批次。"""
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM task_batches WHERE id = ?", (batch_id,)).fetchone()
        if row is None:
            raise ValueError(f"任务批次不存在: {batch_id}")
        batch = dict(row)
        batch["runtime_config"] = _load_runtime_config(batch.get("runtime_config", "{}"))
        return batch

    def list_batches(self) -> list[dict[str, Any]]:
        """按创建顺序倒序返回任务批次，供其他模块选择来源任务。"""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM task_batches
                ORDER BY id DESC
                """
            ).fetchall()
        batches = [dict(row) for row in rows]
        for batch in batches:
            batch["runtime_config"] = _load_runtime_config(batch.get("runtime_config", "{}"))
        return batches

    def list_keyword_tasks(self, batch_id: int) -> list[dict[str, Any]]:
        """按创建顺序返回批次下的关键词任务。"""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM keyword_tasks
                WHERE batch_id = ?
                ORDER BY id
                """,
                (batch_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_next_pending_task(self, batch_id: int) -> dict[str, Any] | None:
        """返回批次中下一条待执行任务。"""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM keyword_tasks
                WHERE batch_id = ? AND status = 'pending'
                ORDER BY id
                LIMIT 1
                """,
                (batch_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_latest_resumable_batch_id(self) -> int | None:
        """返回最近一个仍可继续执行的批次 ID。"""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id
                FROM task_batches
                WHERE status IN ('pending', 'running', 'paused', 'completed_with_errors')
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
        return int(row["id"]) if row else None

    def mark_batch_running(self, batch_id: int) -> None:
        """标记批次运行中。"""
        self._update_batch_status(batch_id, "running")

    def mark_batch_paused(self, batch_id: int) -> None:
        """标记批次暂停。"""
        self._update_batch_status(batch_id, "paused")

    def mark_batch_stopped(self, batch_id: int) -> None:
        """标记批次停止。"""
        self._update_batch_status(batch_id, "stopped")

    def mark_task_running(self, task_id: int) -> None:
        """标记关键词任务运行中。"""
        self._update_task_status(task_id, "running", "")

    def mark_task_succeeded(self, task_id: int) -> None:
        """标记关键词任务成功。"""
        self._update_task_status(task_id, "success", "")

    def mark_task_failed(self, task_id: int, failure_reason: str) -> None:
        """标记关键词任务失败。"""
        self._update_task_status(task_id, "failed", failure_reason)

    def reset_running_tasks_to_pending(self, batch_id: int) -> None:
        """应用重启或暂停恢复前，将未完成的运行中任务还原为待执行。"""
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE keyword_tasks
                SET status = 'pending',
                    updated_at = CURRENT_TIMESTAMP
                WHERE batch_id = ? AND status = 'running'
                """,
                (batch_id,),
            )
            connection.commit()

    def reset_failed_tasks_to_pending(self, batch_id: int) -> int:
        """将批次中的失败任务还原为待执行，用于重试失败关键词。"""
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE keyword_tasks
                SET status = 'pending',
                    failure_reason = '',
                    updated_at = CURRENT_TIMESTAMP
                WHERE batch_id = ? AND status = 'failed'
                """,
                (batch_id,),
            )
            connection.commit()
            return int(cursor.rowcount)

    def refresh_batch_counts(self, batch_id: int) -> None:
        """刷新批次统计和最终状态。"""
        with self._connect() as connection:
            counts = connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
                    SUM(CASE WHEN status IN ('pending', 'running') THEN 1 ELSE 0 END) AS remaining_count
                FROM keyword_tasks
                WHERE batch_id = ?
                """,
                (batch_id,),
            ).fetchone()

            total = int(counts["total"] or 0)
            success_count = int(counts["success_count"] or 0)
            failed_count = int(counts["failed_count"] or 0)
            remaining_count = int(counts["remaining_count"] or 0)
            if remaining_count > 0:
                status = "pending"
            elif failed_count > 0:
                status = "completed_with_errors"
            else:
                status = "completed"

            connection.execute(
                """
                UPDATE task_batches
                SET total_keywords = ?,
                    completed_keywords = ?,
                    failed_keywords = ?,
                    status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (total, success_count, failed_count, status, batch_id),
            )
            connection.commit()

    def _update_batch_status(self, batch_id: int, status: str) -> None:
        """更新批次状态。"""
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE task_batches
                SET status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, batch_id),
            )
            connection.commit()

    def _update_task_status(self, task_id: int, status: str, failure_reason: str) -> None:
        """更新关键词任务状态。"""
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE keyword_tasks
                SET status = ?,
                    failure_reason = ?,
                    last_run_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, failure_reason, task_id),
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        """创建 SQLite 连接。"""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


def _load_runtime_config(value: str) -> dict[str, Any]:
    """从数据库字段读取任务运行参数快照。"""
    try:
        loaded = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}
