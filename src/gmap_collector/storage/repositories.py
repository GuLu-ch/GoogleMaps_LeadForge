import sqlite3
from pathlib import Path
from typing import Any

from gmap_collector.common.models import BusinessRecord


class BusinessRepository:
    """商家记录仓储。

    去重规则集中在这里实现：Google Maps 链接唯一；重复命中时合并来源关键词。
    """

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def upsert_business(self, record: BusinessRecord, keyword_task_id: int | None = None, query_text: str = "") -> int:
        """写入或更新商家记录，并返回商家 ID。

        `keyword_task_id` 和 `query_text` 用于记录商家命中关系；调用方没有任务上下文时可以
        只写主记录，保持导出和去重流程简单。
        """
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            existing = connection.execute(
                "SELECT * FROM businesses WHERE google_maps_url = ?",
                (record.google_maps_url,),
            ).fetchone()

            if existing is None:
                cursor = connection.execute(
                    """
                    INSERT INTO businesses (
                        name, address, phone, website, rating, review_count,
                        category, google_maps_url, source_keywords
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.name,
                        record.address,
                        record.phone,
                        record.website,
                        record.rating,
                        record.review_count,
                        record.category,
                        record.google_maps_url,
                        record.source_keyword,
                    ),
                )
                business_id = int(cursor.lastrowid)
                self._insert_task_hit(connection, business_id, keyword_task_id, query_text)
                connection.commit()
                return business_id

            merged_keywords = _merge_source_keywords(existing["source_keywords"], record.source_keyword)
            connection.execute(
                """
                UPDATE businesses
                SET name = ?,
                    address = ?,
                    phone = ?,
                    website = ?,
                    rating = ?,
                    review_count = ?,
                    category = ?,
                    source_keywords = ?,
                    last_seen_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    record.name or existing["name"],
                    record.address or existing["address"],
                    record.phone or existing["phone"],
                    record.website or existing["website"],
                    record.rating or existing["rating"],
                    record.review_count or existing["review_count"],
                    record.category or existing["category"],
                    merged_keywords,
                    existing["id"],
                ),
            )
            self._insert_task_hit(connection, int(existing["id"]), keyword_task_id, query_text)
            connection.commit()
            return int(existing["id"])

    def list_businesses(self, batch_id: int | None = None) -> list[dict[str, Any]]:
        """按 ID 顺序返回去重后的商家记录。

        `batch_id` 为空时返回全局去重结果；传入批次 ID 时，只返回该任务批次命中的商家。
        """
        where_clause = ""
        parameters: tuple[Any, ...] = ()
        if batch_id is not None:
            where_clause = """
                WHERE businesses.id IN (
                    SELECT business_task_hits.business_id
                    FROM business_task_hits
                    INNER JOIN keyword_tasks ON keyword_tasks.id = business_task_hits.keyword_task_id
                    WHERE keyword_tasks.batch_id = ?
                )
            """
            parameters = (batch_id,)

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                f"""
                SELECT
                    id, name, address, phone, website, rating, review_count,
                    category, google_maps_url, source_keywords,
                    explored_phone, emails, instagram, tiktok, twitter_x,
                    facebook, linkedin, youtube, whatsapp, seo_keywords,
                    website_exploration_status, website_explored_at,
                    first_seen_at, last_seen_at
                FROM businesses
                {where_clause}
                ORDER BY id
                """,
                parameters,
            ).fetchall()

        return [dict(row) for row in rows]

    def get_business_stats(self) -> dict[str, int]:
        """返回任务执行页需要展示的商家统计。"""
        with sqlite3.connect(self.database_path) as connection:
            deduped_businesses = connection.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]
            raw_hits = connection.execute("SELECT COUNT(*) FROM business_task_hits").fetchone()[0]

        return {
            "raw_hits": int(raw_hits or 0),
            "deduped_businesses": int(deduped_businesses or 0),
        }

    def _insert_task_hit(
        self,
        connection: sqlite3.Connection,
        business_id: int,
        keyword_task_id: int | None,
        query_text: str,
    ) -> None:
        """写入商家和关键词任务的命中关系。

        完整搜索词包含城市、地区和逗号，不适合混入 `source_keywords` 的逗号分隔字段，
        因此单独写入命中关系表，便于后续追踪来源。
        """
        if not query_text:
            return
        connection.execute(
            """
            INSERT INTO business_task_hits (business_id, keyword_task_id, query_text)
            VALUES (?, ?, ?)
            """,
            (business_id, keyword_task_id, query_text),
        )


def _merge_source_keywords(existing_keywords: str, new_keyword: str) -> str:
    """合并来源关键词并保持插入顺序。

    用户要求多个来源关键词放在同一个字段中，并用英文逗号分隔。
    """
    keywords: list[str] = []
    for keyword in [*existing_keywords.split(","), new_keyword]:
        cleaned = keyword.strip()
        if cleaned and cleaned not in keywords:
            keywords.append(cleaned)
    return ",".join(keywords)
