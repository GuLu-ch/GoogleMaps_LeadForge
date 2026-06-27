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

    def upsert_business(self, record: BusinessRecord) -> int:
        """写入或更新商家记录，并返回商家 ID。"""
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
                connection.commit()
                return int(cursor.lastrowid)

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
            connection.commit()
            return int(existing["id"])

    def list_businesses(self) -> list[dict[str, Any]]:
        """按 ID 顺序返回全部去重后的商家记录。"""
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT
                    id, name, address, phone, website, rating, review_count,
                    category, google_maps_url, source_keywords, first_seen_at, last_seen_at
                FROM businesses
                ORDER BY id
                """
            ).fetchall()

        return [dict(row) for row in rows]


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
