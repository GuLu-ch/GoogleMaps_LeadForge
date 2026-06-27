from gmap_collector.config.schemas import CityConfig, CountryConfig, RegionConfig
from gmap_collector.tasks.keyword_builder import (
    build_google_maps_search_url,
    build_query_text,
    build_task_inputs,
)


def test_build_query_text_uses_keyword_city_region_country():
    """搜索词应按行业关键词、城市、地区、国家组合。"""
    query_text = build_query_text(
        industry_keyword="Car Wrap Shop",
        city_search_name="Biberach",
        region_search_name="Baden-Wuerttemberg",
        country_search_name="Germany",
    )

    assert query_text == "Car Wrap Shop in Biberach, Baden-Wuerttemberg, Germany"


def test_build_google_maps_search_url_encodes_query_text():
    """Google Maps URL 应对空格和逗号进行编码，便于直接访问。"""
    url = build_google_maps_search_url("Car Wrap Shop in Biberach, Baden-Wuerttemberg, Germany")

    assert url == (
        "https://www.google.com/maps/search/"
        "Car+Wrap+Shop+in+Biberach%2C+Baden-Wuerttemberg%2C+Germany"
    )


def test_build_task_inputs_expands_selected_regions_to_all_cities():
    """选择地区后，应默认包含该地区下全部城市并组合全部关键词。"""
    country = CountryConfig(
        name="德国",
        search_name="Germany",
        regions=(
            RegionConfig(
                name="巴登-符腾堡州",
                search_name="Baden-Wuerttemberg",
                cities=(
                    CityConfig(name="斯图加特", search_name="Stuttgart"),
                    CityConfig(name="比伯拉赫", search_name="Biberach"),
                ),
            ),
        ),
    )

    tasks = build_task_inputs(country=country, selected_region_names={"巴登-符腾堡州"}, industry_keywords=["Car Wrap Shop", "PPF"])

    assert len(tasks) == 4
    assert tasks[0].query_text == "Car Wrap Shop in Stuttgart, Baden-Wuerttemberg, Germany"
    assert tasks[1].query_text == "Car Wrap Shop in Biberach, Baden-Wuerttemberg, Germany"
    assert tasks[2].query_text == "PPF in Stuttgart, Baden-Wuerttemberg, Germany"
    assert tasks[3].query_text == "PPF in Biberach, Baden-Wuerttemberg, Germany"
