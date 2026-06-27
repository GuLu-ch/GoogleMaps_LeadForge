from __future__ import annotations

import argparse
import os
import subprocess
from collections.abc import Callable
from pathlib import Path

from gmap_collector.common.paths import get_project_root, resolve_project_path
from gmap_collector.config.loader import load_app_config


def find_browser_executable(browser_name: str, prefer_chrome_proxy: bool = True) -> Path:
    """查找本机真实浏览器可执行文件。

    登录 Google 账号时不能通过 Selenium WebDriver 启动浏览器，否则可能出现
    “This browser or app may not be secure”。这里直接查找系统安装的 Chrome/Edge
    程序，并在登录脚本中用普通进程启动。
    """
    browser = browser_name.lower()
    candidates: list[Path] = []

    if browser == "chrome":
        chrome_roots = [
            os.environ.get("PROGRAMFILES"),
            os.environ.get("PROGRAMFILES(X86)"),
            os.environ.get("LOCALAPPDATA"),
        ]
        for root in chrome_roots:
            if not root:
                continue
            base_dir = Path(root) / "Google" / "Chrome" / "Application"
            if prefer_chrome_proxy:
                candidates.append(base_dir / "chrome_proxy.exe")
            candidates.append(base_dir / "chrome.exe")
    elif browser == "edge":
        edge_roots = [
            os.environ.get("PROGRAMFILES(X86)"),
            os.environ.get("PROGRAMFILES"),
            os.environ.get("LOCALAPPDATA"),
        ]
        for root in edge_roots:
            if root:
                candidates.append(Path(root) / "Microsoft" / "Edge" / "Application" / "msedge.exe")
    else:
        raise ValueError(f"不支持的浏览器：{browser_name}")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    searched_paths = "\n".join(str(path) for path in candidates)
    raise FileNotFoundError(f"未找到 {browser_name} 浏览器可执行文件，已检查：\n{searched_paths}")


def open_login_browser(
    browser_name: str | None = None,
    login_url: str = "https://accounts.google.com/",
    wait_for_close: Callable[[], str] = input,
    process_factory: Callable[[list[str]], subprocess.Popen] | None = None,
    executable_path: str | Path | None = None,
    prefer_chrome_proxy: bool = True,
) -> None:
    """使用真实浏览器进程打开登录页，并把登录缓存写入项目目录。

    浏览器用户数据目录固定使用 `drivers/selenium-cache/<browser>`，因此在该窗口完成
    Google 登录后，后续 Selenium 采集任务使用同一浏览器时可以复用登录状态。
    """
    project_root = get_project_root()
    app_config = load_app_config(project_root / "config" / "app_config.json")
    selected_browser = (browser_name or app_config.browser.default_browser).lower()
    cache_dir = resolve_project_path(app_config.paths.selenium_cache_dir) / selected_browser
    cache_dir.mkdir(parents=True, exist_ok=True)
    browser_executable = (
        Path(executable_path)
        if executable_path
        else find_browser_executable(selected_browser, prefer_chrome_proxy=prefer_chrome_proxy)
    )

    command = [
        str(browser_executable),
        f"--user-data-dir={cache_dir}",
        "--profile-directory=Default",
        "--no-first-run",
        "--new-window",
        login_url,
    ]
    factory = process_factory or subprocess.Popen
    process = factory(command)

    print(f"已打开 {selected_browser} 登录浏览器。")
    print(f"浏览器程序路径：{browser_executable}")
    print(f"浏览器用户数据目录：{cache_dir}")
    print("请在打开的浏览器中完成 Google 登录。登录完成后回到此窗口按 Enter 关闭浏览器。")
    wait_for_close()

    # 如果用户已经手动关闭浏览器，这里不会重复处理；否则按 Enter 后主动关闭本次登录进程。
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def main() -> None:
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="打开与采集任务共用配置的 Google 登录浏览器。")
    parser.add_argument("--browser", choices=["chrome", "edge"], default=None, help="要打开的浏览器，默认读取配置。")
    parser.add_argument("--url", default="https://accounts.google.com/", help="要打开的登录地址。")
    parser.add_argument("--executable", default=None, help="手动指定浏览器可执行文件路径。")
    parser.add_argument(
        "--no-chrome-proxy",
        action="store_true",
        help="Chrome 登录时不优先使用 chrome_proxy.exe，改为查找 chrome.exe。",
    )
    args = parser.parse_args()

    open_login_browser(
        browser_name=args.browser,
        login_url=args.url,
        executable_path=args.executable,
        prefer_chrome_proxy=not args.no_chrome_proxy,
    )


if __name__ == "__main__":
    main()
