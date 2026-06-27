"""根据本地国家表和城市库生成项目可用的地区配置。

这个脚本用于一次性把用户收集到的真实数据转换成项目当前 GUI 能读取的
`countries -> regions -> cities` 结构。脚本默认生成全部国家，并保留参数方便
后续临时重新生成。
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


DEFAULT_LOCATION_TYPES = {
    "capital",
    "city",
    "locality",
    "municipality",
    "town",
}


@dataclass
class CityBucket:
    """生成过程中的城市临时结构。"""

    name: str
    search_name: str


@dataclass
class RegionBucket:
    """生成过程中的地区临时结构。"""

    name: str
    search_name: str
    code: str
    cities: list[CityBucket] = field(default_factory=list)
    city_keys: set[str] = field(default_factory=set)


@dataclass
class CountryBucket:
    """生成过程中的国家临时结构。"""

    code: str
    name: str
    search_name: str
    regions: dict[tuple[str, str], RegionBucket] = field(default_factory=dict)


class CountryTableParser(HTMLParser):
    """解析 `guojia2.html` 中的国家表格。

    表格每行格式为：中文国家名、英文国家名、旗帜、二字代码、电话代码、时差。
    这里只读取前三个业务字段：中文名、英文名和二字代码。
    """

    def __init__(self) -> None:
        super().__init__()
        self._in_cell = False
        self._current_cell: list[str] = []
        self._current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """进入表格单元格时开始收集文本。"""
        if tag.lower() == "td":
            self._in_cell = True
            self._current_cell = []

    def handle_endtag(self, tag: str) -> None:
        """单元格或行结束时整理已收集文本。"""
        tag = tag.lower()
        if tag == "td" and self._in_cell:
            text = normalize_text("".join(self._current_cell))
            self._current_row.append(text)
            self._in_cell = False
        elif tag == "tr":
            if self._current_row:
                self.rows.append(self._current_row)
            self._current_row = []

    def handle_data(self, data: str) -> None:
        """收集单元格文本内容。"""
        if self._in_cell:
            self._current_cell.append(data)


def normalize_text(value: Any) -> str:
    """把任意输入整理成适合写入配置的单行文本。"""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def parse_country_table(path: str | Path) -> dict[str, dict[str, str]]:
    """读取国家 HTML 表，返回按二字国家代码索引的中英文国家名。"""
    parser = CountryTableParser()
    parser.feed(Path(path).read_text(encoding="utf-8"))

    countries: dict[str, dict[str, str]] = {}
    for row in parser.rows:
        if len(row) < 4:
            continue

        zh_name = normalize_text(row[0])
        search_name = normalize_text(row[1])
        code = normalize_text(row[3]).upper()
        if not zh_name or not search_name or not code:
            continue

        countries[code] = {
            "name": zh_name,
            "search_name": search_name,
        }

    return countries


def load_city_rows(path: str | Path) -> list[dict[str, Any]]:
    """读取城市 JSON 文件，并确保顶层结构是列表。"""
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"城市数据必须是 JSON 数组: {path}")

    return data


def _display_country_name(country_code: str, row: dict[str, Any], country_names: dict[str, dict[str, str]]) -> str:
    """获取国家显示名，优先使用中文国家表，缺失时使用城市库英文名。"""
    mapped = country_names.get(country_code)
    if mapped:
        return mapped["name"]
    return normalize_text(row.get("country_name")) or country_code


def _search_country_name(country_code: str, row: dict[str, Any], country_names: dict[str, dict[str, str]]) -> str:
    """获取国家搜索名，优先使用国家表英文名。"""
    mapped = country_names.get(country_code)
    if mapped:
        return mapped["search_name"]
    return normalize_text(row.get("country_name")) or country_code


def _display_city_name(row: dict[str, Any]) -> str:
    """获取城市显示名，优先使用中文翻译，缺失时回退到英文名。"""
    translations = row.get("translations")
    if isinstance(translations, dict):
        zh_name = normalize_text(translations.get("zh-CN"))
        if zh_name:
            return zh_name
    return normalize_text(row.get("name"))


def _row_type(row: dict[str, Any]) -> str:
    """获取城市库中的地点类型。"""
    return normalize_text(row.get("type"))


def _allowed_country_codes(rows: list[dict[str, Any]], location_types: set[str] | None) -> set[str]:
    """计算默认筛选后仍有地点的国家，用于给缺失国家做兜底。"""
    if location_types is None:
        return {normalize_text(row.get("country_code")).upper() for row in rows if normalize_text(row.get("country_code"))}

    allowed: set[str] = set()
    for row in rows:
        country_code = normalize_text(row.get("country_code")).upper()
        if country_code and _row_type(row) in location_types:
            allowed.add(country_code)
    return allowed


def _should_include_row(
    row: dict[str, Any],
    location_types: set[str] | None,
    countries_with_allowed_rows: set[str],
    fallback_when_country_has_no_allowed_rows: bool,
) -> bool:
    """判断当前城市行是否应该进入配置。"""
    if location_types is None:
        return True

    row_type = _row_type(row)
    if row_type in location_types:
        return True

    if not fallback_when_country_has_no_allowed_rows:
        return False

    country_code = normalize_text(row.get("country_code")).upper()
    return bool(country_code and country_code not in countries_with_allowed_rows)


def _make_region_names_unique(country: CountryBucket) -> dict[tuple[str, str], str]:
    """生成国家内唯一地区显示名，避免 GUI 复选框使用地区名做 key 时互相覆盖。"""
    name_counter = Counter(region.name for region in country.regions.values())
    unique_names: dict[tuple[str, str], str] = {}

    for region_key, region in country.regions.items():
        if name_counter[region.name] <= 1:
            unique_names[region_key] = region.name
            continue

        suffix = region.code or str(region_key[1]) or "重复"
        unique_names[region_key] = f"{region.name} ({suffix})"

    return unique_names


def build_locations_data(
    city_rows: list[dict[str, Any]],
    country_names: dict[str, dict[str, str]],
    location_types: set[str] | None = DEFAULT_LOCATION_TYPES,
    fallback_when_country_has_no_allowed_rows: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """把国家表和城市库转换成项目地区配置结构。"""
    countries: dict[str, CountryBucket] = {}
    countries_with_allowed_rows = _allowed_country_codes(city_rows, location_types)
    summary = {
        "city_rows_total": len(city_rows),
        "city_rows_included": 0,
        "duplicate_city_rows_skipped": 0,
        "missing_country_code_rows_skipped": 0,
        "missing_city_name_rows_skipped": 0,
        "fallback_country_codes": [],
        "location_types": sorted(location_types) if location_types is not None else ["全部类型"],
    }
    fallback_country_codes: set[str] = set()

    for row in city_rows:
        country_code = normalize_text(row.get("country_code")).upper()
        if not country_code:
            summary["missing_country_code_rows_skipped"] += 1
            continue

        include_row = _should_include_row(
            row=row,
            location_types=location_types,
            countries_with_allowed_rows=countries_with_allowed_rows,
            fallback_when_country_has_no_allowed_rows=fallback_when_country_has_no_allowed_rows,
        )
        if not include_row:
            continue

        if location_types is not None and country_code not in countries_with_allowed_rows:
            fallback_country_codes.add(country_code)

        city_search_name = normalize_text(row.get("name"))
        city_display_name = _display_city_name(row)
        if not city_search_name or not city_display_name:
            summary["missing_city_name_rows_skipped"] += 1
            continue

        summary["city_rows_included"] += 1
        country = countries.setdefault(
            country_code,
            CountryBucket(
                code=country_code,
                name=_display_country_name(country_code, row, country_names),
                search_name=_search_country_name(country_code, row, country_names),
            ),
        )

        state_name = normalize_text(row.get("state_name")) or country.search_name
        state_code = normalize_text(row.get("state_code"))
        region_key = (state_name, state_code)
        region = country.regions.setdefault(
            region_key,
            RegionBucket(
                name=state_name,
                search_name=state_name,
                code=state_code,
            ),
        )

        city_key = city_search_name.casefold()
        if city_key in region.city_keys:
            summary["duplicate_city_rows_skipped"] += 1
            continue

        region.city_keys.add(city_key)
        region.cities.append(CityBucket(name=city_display_name, search_name=city_search_name))

    country_name_counter = Counter(country.name for country in countries.values())
    output_countries: list[dict[str, Any]] = []
    region_count = 0
    city_count = 0

    for country in sorted(countries.values(), key=lambda item: (item.name, item.code)):
        display_country_name = country.name
        if country_name_counter[country.name] > 1:
            display_country_name = f"{country.name} ({country.code})"

        unique_region_names = _make_region_names_unique(country)
        output_regions: list[dict[str, Any]] = []
        for region_key, region in sorted(country.regions.items(), key=lambda item: (item[1].name, item[1].code)):
            output_cities = [
                {"name": city.name, "search_name": city.search_name}
                for city in sorted(region.cities, key=lambda item: (item.search_name.casefold(), item.name))
            ]
            if not output_cities:
                continue

            output_regions.append(
                {
                    "name": unique_region_names[region_key],
                    "search_name": region.search_name,
                    "cities": output_cities,
                }
            )
            region_count += 1
            city_count += len(output_cities)

        if not output_regions:
            continue

        output_countries.append(
            {
                "name": display_country_name,
                "search_name": country.search_name,
                "regions": output_regions,
            }
        )

    summary["country_count"] = len(output_countries)
    summary["region_count"] = region_count
    summary["city_count"] = city_count
    summary["fallback_country_codes"] = sorted(fallback_country_codes)

    return {"countries": output_countries}, summary


def write_locations_config(data: dict[str, Any], output_path: str | Path) -> None:
    """把生成后的地区配置写入 JSON 文件。"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="根据本地国家表和城市库生成地区配置")
    parser.add_argument("--country-table", default="tests/guojia/guojia2.html", help="国家 HTML 表路径")
    parser.add_argument("--cities", default="tests/json-cities/cities.json", help="城市 JSON 数据路径")
    parser.add_argument("--output", default="config/locations.json", help="输出配置路径")
    parser.add_argument(
        "--all-types",
        action="store_true",
        help="导入城市库中的全部类型；默认只导入适合搜索的城市类地点，并对空国家兜底",
    )
    parser.add_argument(
        "--type",
        dest="location_types",
        action="append",
        help="指定要导入的地点类型，可重复传入；不传则使用默认城市类地点",
    )
    return parser.parse_args()


def main() -> None:
    """脚本入口。"""
    args = parse_args()
    country_names = parse_country_table(args.country_table)
    city_rows = load_city_rows(args.cities)
    if args.all_types:
        location_types = None
    elif args.location_types:
        location_types = {normalize_text(item) for item in args.location_types if normalize_text(item)}
    else:
        location_types = DEFAULT_LOCATION_TYPES

    data, summary = build_locations_data(
        city_rows=city_rows,
        country_names=country_names,
        location_types=location_types,
    )
    write_locations_config(data, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
