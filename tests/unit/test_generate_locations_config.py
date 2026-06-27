import json
from pathlib import Path

from scripts.generate_locations_config import build_locations_data, parse_country_table


def test_build_locations_data_groups_countries_regions_and_cities(tmp_path: Path):
    """生成地区配置时，应合并国家中文名、地区和城市，并处理重复地区名。"""
    country_html = tmp_path / "countries.html"
    country_html.write_text(
        """
        <table>
          <tr><td>德国</td><td>Germany</td><td>flag</td><td>DE</td></tr>
          <tr><td>测试国</td><td>Testland</td><td>flag</td><td>TL</td></tr>
        </table>
        """,
        encoding="utf-8",
    )
    city_rows = [
        {
            "name": "Munich",
            "state_id": 1,
            "state_code": "BY",
            "state_name": "Bavaria",
            "country_code": "DE",
            "country_name": "Germany",
            "type": "city",
            "translations": {"zh-CN": "慕尼黑"},
        },
        {
            "name": "Munich",
            "state_id": 1,
            "state_code": "BY",
            "state_name": "Bavaria",
            "country_code": "DE",
            "country_name": "Germany",
            "type": "city",
            "translations": {"zh-CN": "慕尼黑"},
        },
        {
            "name": "Alpha",
            "state_id": 10,
            "state_code": "A",
            "state_name": "Central",
            "country_code": "TL",
            "country_name": "Testland",
            "type": "adm2",
            "translations": {"zh-CN": "阿尔法"},
        },
        {
            "name": "Beta",
            "state_id": 11,
            "state_code": "B",
            "state_name": "Central",
            "country_code": "TL",
            "country_name": "Testland",
            "type": "adm3",
            "translations": {},
        },
        {
            "name": "Ghost",
            "state_id": 12,
            "state_code": "G",
            "state_name": "Hidden",
            "country_code": "TL",
            "country_name": "Testland",
            "type": "adm4",
            "translations": {"zh-CN": "幽灵"},
        },
    ]

    country_names = parse_country_table(country_html)
    data, summary = build_locations_data(
        city_rows=city_rows,
        country_names=country_names,
        location_types={"city", "adm2", "adm3"},
    )

    countries = {country["search_name"]: country for country in data["countries"]}
    germany = countries["Germany"]
    testland = countries["Testland"]

    assert germany["name"] == "德国"
    assert germany["regions"][0]["name"] == "Bavaria"
    assert germany["regions"][0]["cities"] == [{"name": "慕尼黑", "search_name": "Munich"}]
    assert [region["name"] for region in testland["regions"]] == ["Central (A)", "Central (B)"]
    assert testland["regions"][1]["cities"][0] == {"name": "Beta", "search_name": "Beta"}
    assert summary["city_rows_total"] == 5
    assert summary["city_rows_included"] == 4
    assert summary["duplicate_city_rows_skipped"] == 1


def test_build_locations_data_can_write_json_shape(tmp_path: Path):
    """生成结果应保持 config 目录当前加载器使用的 JSON 结构。"""
    data, _summary = build_locations_data(
        city_rows=[
            {
                "name": "Fallback City",
                "state_id": 2,
                "state_code": "",
                "state_name": "Fallback State",
                "country_code": "XX",
                "country_name": "Fallback Country",
                "type": None,
                "translations": {},
            }
        ],
        country_names={},
        location_types=None,
    )
    output_path = tmp_path / "locations.json"
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    saved = json.loads(output_path.read_text(encoding="utf-8"))

    assert list(saved) == ["countries"]
    assert saved["countries"][0]["name"] == "Fallback Country"
    assert saved["countries"][0]["regions"][0]["cities"][0]["search_name"] == "Fallback City"
