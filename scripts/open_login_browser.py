from __future__ import annotations

import argparse
from collections.abc import Callable

from gmap_collector.browser.selenium_engine import SeleniumBrowserEngine
from gmap_collector.common.paths import get_project_root, resolve_project_path
from gmap_collector.config.loader import load_app_config


def open_login_browser(
    browser_name: str | None = None,
    login_url: str = "https://accounts.google.com/",
    wait_for_close: Callable[[], str] = input,
    engine_factory=SeleniumBrowserEngine,
) -> None:
    """使用采集任务同一套 Selenium 浏览器配置打开登录页。

    浏览器用户数据目录固定使用 `drivers/selenium-cache/<browser>`，因此在该窗口完成
    Google 登录后，后续采集任务使用同一浏览器时可以复用登录状态。
    """
    project_root = get_project_root()
    app_config = load_app_config(project_root / "config" / "app_config.json")
    selected_browser = (browser_name or app_config.browser.default_browser).lower()
    cache_dir = resolve_project_path(app_config.paths.selenium_cache_dir) / selected_browser

    engine = engine_factory(
        browser_name=selected_browser,
        page_load_timeout_seconds=app_config.crawler.page_load_timeout_seconds,
        cache_dir=cache_dir,
    )
    engine.start()
    engine.open_url(login_url)

    print(f"已打开 {selected_browser} 登录浏览器。")
    print(f"浏览器用户数据目录：{cache_dir}")
    print("请在打开的浏览器中完成 Google 登录。登录完成后回到此窗口按 Enter 关闭浏览器。")
    wait_for_close()
    engine.close()


def main() -> None:
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="打开与采集任务共用配置的 Google 登录浏览器。")
    parser.add_argument("--browser", choices=["chrome", "edge"], default=None, help="要打开的浏览器，默认读取配置。")
    parser.add_argument("--url", default="https://accounts.google.com/", help="要打开的登录地址。")
    args = parser.parse_args()

    open_login_browser(browser_name=args.browser, login_url=args.url)


if __name__ == "__main__":
    main()
