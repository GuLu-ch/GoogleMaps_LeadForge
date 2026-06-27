from pathlib import Path


def test_selenium_wait_condition_does_not_depend_on_ui_language():
    """等待 Google Maps 结果时不能依赖中文或英文界面文案。"""
    source = Path("src/gmap_collector/browser/selenium_engine.py").read_text(encoding="utf-8")

    assert "innerText.includes" not in source
    assert "結果" not in source
    assert "Results" not in source
    assert "div[role=\"feed\"]" in source
    assert "a[href*=\"/maps/place/\"]" in source
