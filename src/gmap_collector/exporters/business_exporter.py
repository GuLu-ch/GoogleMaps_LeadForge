from pathlib import Path

import pandas as pd

from gmap_collector.storage.repositories import BusinessRepository


EXPORT_COLUMNS = {
    "name": "商家名称",
    "address": "地址",
    "phone": "电话",
    "explored_phone": "官网探索电话",
    "emails": "Email",
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "twitter_x": "Twitter / X",
    "facebook": "Facebook",
    "linkedin": "LinkedIn",
    "youtube": "YouTube",
    "whatsapp": "WhatsApp",
    "seo_keywords": "SEO Keywords",
    "website_exploration_status": "官网探索状态",
    "website_explored_at": "官网探索时间",
    "website": "官网",
    "rating": "评分",
    "review_count": "评论数量",
    "category": "商家分类",
    "google_maps_url": "Google Maps 链接",
    "source_keywords": "来源关键词",
    "first_seen_at": "首次采集时间",
    "last_seen_at": "最后更新时间",
}


def export_businesses_to_csv(
    database_path: str | Path,
    output_path: str | Path,
    encoding: str = "utf-8-sig",
    batch_id: int | None = None,
) -> Path:
    """从 SQLite 去重结果导出 CSV。"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    dataframe = _load_business_dataframe(database_path, batch_id=batch_id)
    dataframe.to_csv(output, index=False, encoding=encoding)
    return output


def export_businesses_to_excel(
    database_path: str | Path,
    output_path: str | Path,
    batch_id: int | None = None,
) -> Path:
    """从 SQLite 去重结果导出 Excel。"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    dataframe = _load_business_dataframe(database_path, batch_id=batch_id)
    dataframe.to_excel(output, index=False)
    return output


def _load_business_dataframe(database_path: str | Path, batch_id: int | None = None) -> pd.DataFrame:
    """读取商家记录并转换成导出表格。

    导出层不接收临时内存列表，始终从数据库读取，确保导出结果和全局去重状态一致。
    """
    repository = BusinessRepository(database_path)
    records = repository.list_businesses(batch_id=batch_id)
    dataframe = pd.DataFrame(records)

    if dataframe.empty:
        return pd.DataFrame(columns=list(EXPORT_COLUMNS.values()))

    return dataframe[list(EXPORT_COLUMNS.keys())].rename(columns=EXPORT_COLUMNS)
