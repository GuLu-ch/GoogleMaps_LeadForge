from PySide6.QtCore import QSize
from qfluentwidgets import FluentIcon, FluentWindow

from gmap_collector.config.loader import load_app_config
from gmap_collector.common.paths import get_project_root
from gmap_collector.gui.result_page import ResultPage
from gmap_collector.gui.settings_page import SettingsPage
from gmap_collector.gui.task_config_page import TaskConfigPage
from gmap_collector.gui.task_run_page import TaskRunPage


class MainWindow(FluentWindow):
    """应用主窗口。

    使用 PySide6-Fluent-Widgets 的左侧导航承载四个核心页面。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoogleMaps_LeadForge")
        self.setMinimumSize(QSize(1100, 720))
        self.resize(QSize(1280, 820))
        self._init_pages()

    def _init_pages(self) -> None:
        """初始化左侧导航页面。"""
        project_root = get_project_root()
        app_config = load_app_config(project_root / "config" / "app_config.json")

        self.task_config_page = TaskConfigPage(app_config=app_config, parent=self)
        self.task_run_page = TaskRunPage(self)
        self.result_page = ResultPage(self)
        self.settings_page = SettingsPage(project_root=project_root, app_config=app_config, parent=self)

        self.addSubInterface(self.task_config_page, FluentIcon.EDIT, "任务配置")
        self.addSubInterface(self.task_run_page, FluentIcon.PLAY, "任务执行")
        self.addSubInterface(self.result_page, FluentIcon.VIEW, "结果管理")
        self.addSubInterface(self.settings_page, FluentIcon.SETTING, "设置与文档")
