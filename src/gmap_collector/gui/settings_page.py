from pathlib import Path

from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, ComboBox, LineEdit, PrimaryPushButton, PushButton, SpinBox

from gmap_collector.config.schemas import AppConfig
from gmap_collector.gui.layout_utils import build_action_bar, build_adaptive_page


class SettingsPage(QWidget):
    """设置与文档页。

    该页面聚合全局基础配置，避免用户在多个页面之间来回寻找常用设置。
    """

    def __init__(self, project_root: Path, app_config: AppConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self.project_root = project_root
        self.app_config = app_config
        self.setObjectName("settingsPage")
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout, _, content_root_layout = build_adaptive_page(self)

        runtime_form = QFormLayout()
        runtime_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.browser_combo = ComboBox()
        self.browser_combo.addItems([browser.title() for browser in self.app_config.browser.supported_browsers])
        self.browser_combo.setCurrentText(self.app_config.browser.default_browser.title())
        self.engine_combo = ComboBox()
        self.engine_combo.addItems([engine.title() for engine in self.app_config.browser.supported_engines])
        self.engine_combo.setCurrentText(self.app_config.browser.default_engine.title())
        self.page_initial_wait_spin = SpinBox()
        self.page_initial_wait_spin.setRange(0, 300)
        self.page_initial_wait_spin.setValue(self.app_config.crawler.page_initial_wait_seconds)
        self.keyword_wait_min_spin = SpinBox()
        self.keyword_wait_min_spin.setRange(0, 600)
        self.keyword_wait_min_spin.setValue(self.app_config.crawler.keyword_wait_seconds_min)
        self.keyword_wait_max_spin = SpinBox()
        self.keyword_wait_max_spin.setRange(0, 600)
        self.keyword_wait_max_spin.setValue(self.app_config.crawler.keyword_wait_seconds_max)
        self.scroll_wait_min_spin = SpinBox()
        self.scroll_wait_min_spin.setRange(0, 120)
        self.scroll_wait_min_spin.setValue(self.app_config.crawler.scroll_wait_seconds_min)
        self.scroll_wait_max_spin = SpinBox()
        self.scroll_wait_max_spin.setRange(0, 120)
        self.scroll_wait_max_spin.setValue(self.app_config.crawler.scroll_wait_seconds_max)
        self.max_scroll_rounds_spin = SpinBox()
        self.max_scroll_rounds_spin.setRange(1, 500)
        self.max_scroll_rounds_spin.setValue(self.app_config.crawler.max_scroll_rounds)
        self.no_new_results_spin = SpinBox()
        self.no_new_results_spin.setRange(1, 50)
        self.no_new_results_spin.setValue(self.app_config.crawler.max_no_new_results_rounds)
        self.page_timeout_spin = SpinBox()
        self.page_timeout_spin.setRange(5, 600)
        self.page_timeout_spin.setValue(self.app_config.crawler.page_load_timeout_seconds)
        self.failure_threshold_spin = SpinBox()
        self.failure_threshold_spin.setRange(1, 100)
        self.failure_threshold_spin.setValue(self.app_config.crawler.consecutive_failure_pause_threshold)

        runtime_form.addRow("默认浏览器", self.browser_combo)
        runtime_form.addRow("默认自动化引擎", self.engine_combo)
        runtime_form.addRow("页面初始停留秒数", self.page_initial_wait_spin)
        runtime_form.addRow("关键词停留最小秒数", self.keyword_wait_min_spin)
        runtime_form.addRow("关键词停留最大秒数", self.keyword_wait_max_spin)
        runtime_form.addRow("滚动停留最小秒数", self.scroll_wait_min_spin)
        runtime_form.addRow("滚动停留最大秒数", self.scroll_wait_max_spin)
        runtime_form.addRow("最大滚动次数", self.max_scroll_rounds_spin)
        runtime_form.addRow("连续无新增停止次数", self.no_new_results_spin)
        runtime_form.addRow("页面加载超时秒数", self.page_timeout_spin)
        runtime_form.addRow("连续失败暂停阈值", self.failure_threshold_spin)

        content_root_layout.addWidget(BodyLabel("全局运行设置"))
        content_root_layout.addLayout(runtime_form)

        path_form = QFormLayout()
        path_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.app_config_path_input = self._readonly_path_input("config/app_config.json")
        self.locations_path_input = self._readonly_path_input("config/locations.de.json")
        self.database_path_input = self._readonly_path_input(str(self.app_config.paths.database))
        self.export_dir_input = self._readonly_path_input(str(self.app_config.paths.export_dir))
        self.log_dir_input = self._readonly_path_input(str(self.app_config.paths.log_dir))
        self.selenium_cache_input = self._readonly_path_input(str(self.app_config.paths.selenium_cache_dir))
        self.playwright_browsers_input = self._readonly_path_input(str(self.app_config.paths.playwright_browsers_dir))
        for path_input in [
            self.app_config_path_input,
            self.locations_path_input,
            self.database_path_input,
            self.export_dir_input,
            self.log_dir_input,
            self.selenium_cache_input,
            self.playwright_browsers_input,
        ]:
            path_input.setReadOnly(True)

        path_form.addRow("运行配置文件", self.app_config_path_input)
        path_form.addRow("地区配置文件", self.locations_path_input)
        path_form.addRow("SQLite 数据库", self.database_path_input)
        path_form.addRow("导出目录", self.export_dir_input)
        path_form.addRow("日志目录", self.log_dir_input)
        path_form.addRow("Selenium 缓存目录", self.selenium_cache_input)
        path_form.addRow("Playwright 浏览器目录", self.playwright_browsers_input)

        content_root_layout.addWidget(BodyLabel("项目路径"))
        content_root_layout.addLayout(path_form)

        docs_form = QFormLayout()
        docs_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        paths = [
            ("README", "README.md"),
            ("智能体规范", "AGENTS.md"),
            ("需求文档", "docs/REQUIREMENTS.md"),
            ("设计文档", "docs/DESIGN.md"),
            ("项目结构", "docs/PROJECT_STRUCTURE.md"),
        ]
        for label, relative_path in paths:
            docs_input = self._readonly_path_input(relative_path)
            docs_form.addRow(label, docs_input)

        content_root_layout.addWidget(BodyLabel("项目文档"))
        content_root_layout.addLayout(docs_form)

        action_layout = build_action_bar(root_layout)
        self.save_settings_button = PrimaryPushButton("保存全局设置")
        self.restore_default_button = PushButton("恢复默认设置")
        self.open_config_button = PushButton("打开配置目录")
        self.open_export_button = PushButton("打开导出目录")
        self.open_log_button = PushButton("打开日志目录")
        for button in [
            self.save_settings_button,
            self.restore_default_button,
            self.open_config_button,
            self.open_export_button,
            self.open_log_button,
        ]:
            action_layout.addWidget(button)
        action_layout.addStretch(1)

    def _readonly_path_input(self, relative_path: str) -> LineEdit:
        """创建只读路径输入框。

        PySide6-Fluent-Widgets 的 `LineEdit` 构造函数只接收父组件，文本需要通过
        `setText()` 设置，因此统一封装在这里，避免页面里重复写初始化细节。
        """
        path_input = LineEdit()
        path_input.setText(str(self.project_root / relative_path))
        path_input.setReadOnly(True)
        return path_input
