from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class BrowserPageSnapshot:
    """浏览器页面快照。

    解析层只依赖快照中的 HTML，不依赖 Selenium 或 Playwright 对象，避免跨层耦合。
    """

    html: str
    current_url: str


class BrowserEngine(ABC):
    """浏览器引擎统一接口。

    Selenium 和 Playwright 都必须实现这个接口。任务调度层只依赖该抽象接口，
    不关心底层使用哪一种自动化库。
    """

    @abstractmethod
    def start(self) -> None:
        """启动可视化浏览器。"""

    @abstractmethod
    def close(self) -> None:
        """关闭浏览器并释放资源。"""

    @abstractmethod
    def open_url(self, url: str) -> None:
        """打开指定 URL。"""

    def wait_for_results(self, timeout_seconds: int = 20) -> bool:
        """等待搜索结果区域加载完成。

        不是所有浏览器引擎都必须实现专门等待逻辑；默认返回 True，表示由
        具体引擎或测试替身自行决定是否覆盖该行为。
        """
        return True

    def wait_for_page_ready(self, timeout_seconds: int = 20) -> bool:
        """等待普通网页 DOM 加载完成。

        官网探索兜底只需要拿到当前页面 HTML，不依赖 Google Maps 的结果列表元素。
        默认返回 True，具体浏览器引擎可覆盖为更严格的等待逻辑。
        """
        return True

    @abstractmethod
    def get_snapshot(self) -> BrowserPageSnapshot:
        """返回当前页面 HTML 快照。"""

    @abstractmethod
    def scroll_results(self) -> None:
        """滚动 Google Maps 搜索结果列表。"""

    @abstractmethod
    def is_at_results_bottom(self) -> bool:
        """判断搜索结果列表是否已经到底。"""
