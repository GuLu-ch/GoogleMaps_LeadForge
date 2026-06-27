from pathlib import Path

from scripts.open_login_browser import find_browser_executable, open_login_browser


def test_find_browser_executable_prefers_chrome_proxy(tmp_path, monkeypatch):
    """查找 Chrome 时应优先使用 chrome_proxy.exe，降低 Google 登录被拦截的概率。"""
    application_dir = tmp_path / "Google" / "Chrome" / "Application"
    application_dir.mkdir(parents=True)
    chrome_proxy = application_dir / "chrome_proxy.exe"
    chrome = application_dir / "chrome.exe"
    chrome_proxy.write_text("", encoding="utf-8")
    chrome.write_text("", encoding="utf-8")

    monkeypatch.setenv("PROGRAMFILES", str(tmp_path))
    monkeypatch.delenv("PROGRAMFILES(X86)", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    assert find_browser_executable("chrome") == chrome_proxy


def test_open_login_browser_uses_real_browser_process_and_shared_cache(tmp_path):
    """登录浏览器应启动真实 Chrome 进程，并复用采集任务的用户数据目录。"""
    fake_executable = tmp_path / "chrome_proxy.exe"
    fake_executable.write_text("", encoding="utf-8")
    created_processes = []

    class FakeProcess:
        """测试用浏览器进程，避免单元测试真的打开浏览器。"""

        def __init__(self, command):
            self.command = command
            self.terminated = False
            created_processes.append(self)

        def poll(self):
            return None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            return 0

    open_login_browser(
        browser_name="chrome",
        login_url="https://accounts.google.com/",
        wait_for_close=lambda: "",
        process_factory=FakeProcess,
        executable_path=fake_executable,
    )

    assert len(created_processes) == 1
    command = created_processes[0].command
    user_data_dirs = [arg.removeprefix("--user-data-dir=") for arg in command if arg.startswith("--user-data-dir=")]
    assert Path(command[0]) == fake_executable
    assert len(user_data_dirs) == 1
    assert Path(user_data_dirs[0]).parts[-3:] == ("drivers", "selenium-cache", "chrome")
    assert "--enable-automation" not in command
    assert "https://accounts.google.com/" in command
    assert created_processes[0].terminated is True
