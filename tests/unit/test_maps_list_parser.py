from gmap_collector.parsers.maps_list_parser import parse_maps_list_results


def test_parse_maps_list_results_extracts_business_fields_from_card_html():
    """解析器应从 Google Maps 结果卡片中提取可见商家字段。"""
    html = """
    <div role="feed">
      <div role="article">
        <a href="https://www.google.com/maps/place/Folie+Studio/@52.1,13.1,17z/data=!4m6">Folie Studio</a>
        <span aria-label="4.8 stars">4.8</span>
        <span aria-label="128 reviews">(128)</span>
        <div>Car wrapping service</div>
        <div>Hauptstrasse 12, Berlin, Germany</div>
        <a href="tel:+493012345678">+49 30 12345678</a>
        <a href="https://folie.example">Website</a>
      </div>
    </div>
    """

    records = parse_maps_list_results(html, source_keyword="Car Wrap Shop")

    assert len(records) == 1
    assert records[0].name == "Folie Studio"
    assert records[0].address == "Hauptstrasse 12, Berlin, Germany"
    assert records[0].phone == "+49 30 12345678"
    assert records[0].website == "https://folie.example"
    assert records[0].rating == "4.8"
    assert records[0].review_count == "128"
    assert records[0].category == "Car wrapping service"
    assert records[0].google_maps_url.startswith("https://www.google.com/maps/place/Folie+Studio")
    assert records[0].source_keyword == "Car Wrap Shop"


def test_parse_maps_list_results_leaves_missing_fields_empty():
    """卡片缺少电话、官网或评分时，解析器应保留空字段。"""
    html = """
    <div role="feed">
      <div role="article">
        <a href="https://www.google.com/maps/place/Tint+Point/data=!4m6">Tint Point</a>
        <div>Window tinting service</div>
      </div>
    </div>
    """

    records = parse_maps_list_results(html, source_keyword="Window Tint")

    assert len(records) == 1
    assert records[0].name == "Tint Point"
    assert records[0].phone == ""
    assert records[0].website == ""
    assert records[0].rating == ""
    assert records[0].review_count == ""
    assert records[0].category == "Window tinting service"
