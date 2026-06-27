from dataclasses import dataclass
from urllib.parse import quote_plus

from gmap_collector.config.schemas import CountryConfig


GOOGLE_MAPS_SEARCH_BASE_URL = "https://www.google.com/maps/search/"


@dataclass(frozen=True)
class KeywordTaskInput:
    """创建关键词任务前的纯数据对象。

    该对象不依赖数据库，便于 GUI 预览任务，也便于后续批量写入 SQLite。
    """

    industry_keyword: str
    country_name: str
    country_search_name: str
    region_name: str
    region_search_name: str
    city_name: str
    city_search_name: str
    query_text: str
    search_url: str


def build_query_text(
    industry_keyword: str,
    city_search_name: str,
    region_search_name: str,
    country_search_name: str,
) -> str:
    """组合 Google Maps 搜索词。

    第一版不包含街道级搜索，固定使用“行业关键词 in 城市, 地区, 国家”的结构。
    """
    keyword = industry_keyword.strip()
    return f"{keyword} in {city_search_name}, {region_search_name}, {country_search_name}"


def build_google_maps_search_url(query_text: str) -> str:
    """根据搜索词生成 Google Maps 搜索 URL。"""
    return f"{GOOGLE_MAPS_SEARCH_BASE_URL}{quote_plus(query_text)}"


def build_task_inputs(
    country: CountryConfig,
    selected_region_names: set[str],
    industry_keywords: list[str],
) -> list[KeywordTaskInput]:
    """根据国家、已选地区和行业关键词生成任务输入。

    用户选择地区后，第一版默认展开该地区下的全部城市。
    空关键词会被忽略，避免生成无效任务。
    """
    cleaned_keywords = [keyword.strip() for keyword in industry_keywords if keyword.strip()]
    task_inputs: list[KeywordTaskInput] = []

    for keyword in cleaned_keywords:
        for region in country.regions:
            if region.name not in selected_region_names:
                continue

            for city in region.cities:
                query_text = build_query_text(
                    industry_keyword=keyword,
                    city_search_name=city.search_name,
                    region_search_name=region.search_name,
                    country_search_name=country.search_name,
                )
                task_inputs.append(
                    KeywordTaskInput(
                        industry_keyword=keyword,
                        country_name=country.name,
                        country_search_name=country.search_name,
                        region_name=region.name,
                        region_search_name=region.search_name,
                        city_name=city.name,
                        city_search_name=city.search_name,
                        query_text=query_text,
                        search_url=build_google_maps_search_url(query_text),
                    )
                )

    return task_inputs
