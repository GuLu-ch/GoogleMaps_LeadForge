from pathlib import Path

from scripts.cleanup_runtime_data import cleanup_runtime_data


def test_cleanup_runtime_data_removes_runtime_outputs_and_keeps_inputs(tmp_path):
    """清理脚本应删除运行产物，但保留关键词输入和目录占位文件。"""
    (tmp_path / "data").mkdir()
    (tmp_path / "logs").mkdir()
    (tmp_path / "exports").mkdir()
    (tmp_path / "outputs").mkdir()
    (tmp_path / "debug").mkdir()
    (tmp_path / "temp").mkdir()
    (tmp_path / "screenshots").mkdir()

    for relative_path in [
        "data/app.sqlite3",
        "data/app.sqlite3-wal",
        "logs/run.log",
        "exports/result.csv",
        "outputs/page.html",
        "debug/debug.txt",
        "temp/tmp.txt",
        "screenshots/page.png",
    ]:
        path = tmp_path / relative_path
        path.write_text("运行产物", encoding="utf-8")

    for relative_path in ["logs/.gitkeep", "exports/.gitkeep", "keyword.txt"]:
        path = tmp_path / relative_path
        path.write_text("保留文件", encoding="utf-8")

    removed_paths = cleanup_runtime_data(project_root=tmp_path)

    assert (tmp_path / "keyword.txt").exists()
    assert (tmp_path / "logs/.gitkeep").exists()
    assert (tmp_path / "exports/.gitkeep").exists()
    assert not (tmp_path / "data/app.sqlite3").exists()
    assert not (tmp_path / "logs/run.log").exists()
    assert not (tmp_path / "outputs").exists()
    assert Path("data/app.sqlite3") in removed_paths
    assert Path("outputs") in removed_paths


def test_cleanup_runtime_data_can_remove_browser_cache_when_requested(tmp_path):
    """需要全新测试环境时，清理函数应可选删除浏览器用户缓存。"""
    browser_cache_dir = tmp_path / "drivers" / "selenium-cache" / "chrome"
    browser_cache_dir.mkdir(parents=True)
    (browser_cache_dir / "Cookies").write_text("登录缓存", encoding="utf-8")

    removed_paths = cleanup_runtime_data(project_root=tmp_path, include_browser_cache=True)

    assert not (tmp_path / "drivers" / "selenium-cache").exists()
    assert Path("drivers/selenium-cache") in removed_paths
