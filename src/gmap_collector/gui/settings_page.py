from pathlib import Path

from PySide6.QtWidgets import QWidget
from qfluentwidgets import (
    ComboBox,
    FluentIcon,
    PrimaryPushButton,
    PushButton,
    SettingCard,
    SettingCardGroup,
    Theme,
    setTheme,
)

from gmap_collector.config.schemas import AppConfig
from gmap_collector.gui.fluent_components import NoWheelSpinBox, create_path_card
from gmap_collector.gui.layout_utils import build_action_bar, build_adaptive_page


class SettingsPage(QWidget):
    """设置页。

    该页面只承载全局默认配置、项目路径、维护操作和外观设置。本次任务参数仍在
    “任务配置”页中编辑，并在创建批次时保存为任务快照。
    """

    def __init__(self, project_root: Path, app_config: AppConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self.project_root = project_root
        self.app_config = app_config
        self.path_cards = {}
        self.setObjectName("settingsPage")
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        root_layout, _, content_root_layout = build_adaptive_page(self)

        self.appearance_group = SettingCardGroup("外观", self)
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["跟随系统", "亮色", "暗色"])
        self.theme_combo.setCurrentText("跟随系统")
        self.appearance_group.addSettingCard(
            self._combo_card(
                title="颜色方案",
                content="切换软件的亮色、暗色或跟随系统主题。",
                icon=FluentIcon.BRUSH,
                combo_box=self.theme_combo,
            )
        )
        content_root_layout.addWidget(self.appearance_group)

        self.runtime_group = SettingCardGroup("全局运行设置", self)
        self.browser_combo = ComboBox()
        self.browser_combo.addItems([browser.title() for browser in self.app_config.browser.supported_browsers])
        self.browser_combo.setCurrentText(self.app_config.browser.default_browser.title())
        self.engine_combo = ComboBox()
        self.engine_combo.addItems([engine.title() for engine in self.app_config.browser.supported_engines])
        self.engine_combo.setCurrentText(self.app_config.browser.default_engine.title())

        self.page_initial_wait_spin = self._spin_box(0, 300, self.app_config.crawler.page_initial_wait_seconds)
        self.keyword_wait_min_spin = self._spin_box(0, 600, self.app_config.crawler.keyword_wait_seconds_min)
        self.keyword_wait_max_spin = self._spin_box(0, 600, self.app_config.crawler.keyword_wait_seconds_max)
        self.scroll_wait_min_spin = self._spin_box(0, 120, self.app_config.crawler.scroll_wait_seconds_min)
        self.scroll_wait_max_spin = self._spin_box(0, 120, self.app_config.crawler.scroll_wait_seconds_max)
        self.max_scroll_rounds_spin = self._spin_box(1, 500, self.app_config.crawler.max_scroll_rounds)
        self.no_new_results_spin = self._spin_box(1, 50, self.app_config.crawler.max_no_new_results_rounds)
        self.page_timeout_spin = self._spin_box(5, 600, self.app_config.crawler.page_load_timeout_seconds)
        self.failure_threshold_spin = self._spin_box(1, 100, self.app_config.crawler.consecutive_failure_pause_threshold)

        self.runtime_group.addSettingCards(
            [
                self._combo_card("默认浏览器", "创建新任务时默认使用的浏览器。", FluentIcon.APPLICATION, self.browser_combo),
                self._combo_card("默认自动化引擎", "第一版采集执行使用 Selenium，Playwright 保留为后续扩展。", FluentIcon.ROBOT, self.engine_combo),
                self._spin_card("页面初始停留秒数", "打开 Google Maps 页面后的基础等待时间。", self.page_initial_wait_spin),
                self._spin_card("关键词停留最小秒数", "每个关键词完成后随机等待的最小值。", self.keyword_wait_min_spin),
                self._spin_card("关键词停留最大秒数", "每个关键词完成后随机等待的最大值。", self.keyword_wait_max_spin),
                self._spin_card("滚动停留最小秒数", "列表滚动加载商家时随机等待的最小值。", self.scroll_wait_min_spin),
                self._spin_card("滚动停留最大秒数", "列表滚动加载商家时随机等待的最大值。", self.scroll_wait_max_spin),
                self._spin_card("最大滚动次数", "单个搜索页面最多向下滚动的次数。", self.max_scroll_rounds_spin),
                self._spin_card("连续无新增停止次数", "连续几轮没有新增商家后停止滚动。", self.no_new_results_spin),
                self._spin_card("页面加载超时秒数", "浏览器等待页面加载完成的最长时间。", self.page_timeout_spin),
                self._spin_card("连续失败暂停阈值", "连续失败达到阈值后自动暂停整个任务。", self.failure_threshold_spin),
            ]
        )
        content_root_layout.addWidget(self.runtime_group)

        self.path_group = SettingCardGroup("项目路径", self)
        self._add_path_card("运行配置文件", "config/app_config.json")
        self._add_path_card("地区配置文件", "config/locations.json")
        self._add_path_card("SQLite 数据库", self.app_config.paths.database)
        self._add_path_card("导出目录", self.app_config.paths.export_dir)
        self._add_path_card("日志目录", self.app_config.paths.log_dir)
        self._add_path_card("Selenium 缓存目录", self.app_config.paths.selenium_cache_dir)
        self._add_path_card("Playwright 浏览器目录", self.app_config.paths.playwright_browsers_dir)
        content_root_layout.addWidget(self.path_group)

        self.maintenance_group = SettingCardGroup("维护", self)
        self.clear_runtime_data_button = PushButton("清空数据库和缓存")
        clear_card = SettingCard(
            FluentIcon.BROOM,
            "清空运行数据",
            "删除 SQLite 数据库、日志、导出文件、调试输出和浏览器缓存，重新开始测试。",
            self.maintenance_group,
        )
        clear_card.hBoxLayout.addWidget(self.clear_runtime_data_button)
        clear_card.hBoxLayout.addSpacing(16)
        self.maintenance_group.addSettingCard(clear_card)
        content_root_layout.addWidget(self.maintenance_group)

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

    def _connect_signals(self) -> None:
        """连接设置页内部交互。"""
        self.theme_combo.currentTextChanged.connect(self._apply_theme)

    def _apply_theme(self, theme_text: str) -> None:
        """根据下拉框选择切换应用主题。"""
        theme_map = {
            "亮色": Theme.LIGHT,
            "暗色": Theme.DARK,
            "跟随系统": Theme.AUTO,
        }
        setTheme(theme_map.get(theme_text, Theme.AUTO))

    def _spin_box(self, minimum: int, maximum: int, value: int) -> NoWheelSpinBox:
        """创建设置页通用数字输入框。"""
        spin_box = NoWheelSpinBox()
        spin_box.setRange(minimum, maximum)
        spin_box.setValue(value)
        spin_box.setFixedWidth(120)
        return spin_box

    def _combo_card(self, title: str, content: str, icon: FluentIcon, combo_box: ComboBox) -> SettingCard:
        """创建带下拉选择框的设置卡片。"""
        card = SettingCard(icon, title, content, self)
        combo_box.setMinimumWidth(150)
        card.hBoxLayout.addWidget(combo_box)
        card.hBoxLayout.addSpacing(16)
        return card

    def _spin_card(self, title: str, content: str, spin_box: NoWheelSpinBox) -> SettingCard:
        """创建带数字输入框的设置卡片。"""
        card = SettingCard(FluentIcon.STOP_WATCH, title, content, self)
        card.hBoxLayout.addWidget(spin_box)
        card.hBoxLayout.addSpacing(16)
        return card

    def _add_path_card(self, title: str, relative_path: str | Path) -> None:
        """向路径分组添加一个只读路径卡片。"""
        card = create_path_card(title, self.project_root / relative_path)
        self.path_cards[title] = card
        self.path_group.addSettingCard(card)
