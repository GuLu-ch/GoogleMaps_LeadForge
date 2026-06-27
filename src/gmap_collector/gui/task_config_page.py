from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, CheckBox, ComboBox, LineEdit, PlainTextEdit, PrimaryPushButton, PushButton, SpinBox

from gmap_collector.config.schemas import AppConfig, LocationsConfig
from gmap_collector.gui.layout_utils import build_action_bar, build_adaptive_page
from gmap_collector.gui.table_utils import apply_mixed_table_resize
from gmap_collector.tasks.keyword_builder import KeywordTaskInput, build_task_inputs


class TaskConfigPage(QWidget):
    """任务配置页。

    该页面负责地区选择、关键词输入、运行参数配置和任务预览。创建任务时，主窗口会把
    当前运行参数保存为本次任务快照。
    """

    def __init__(self, app_config: AppConfig, locations_config: LocationsConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self.app_config = app_config
        self.locations_config = locations_config
        self.region_checkboxes: dict[str, CheckBox] = {}
        self.preview_tasks: list[KeywordTaskInput] = []
        self.setObjectName("taskConfigPage")
        self._build_ui()
        self._connect_signals()
        self.select_all_regions()

    def _build_ui(self) -> None:
        root_layout, _, content_root_layout = build_adaptive_page(self)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        region_panel = QVBoxLayout()
        region_panel.addWidget(BodyLabel("国家和地区"))
        self.country_combo = ComboBox()
        self.country_combo.addItems([country.name for country in self.locations_config.countries])
        region_panel.addWidget(self.country_combo)
        self.select_all_regions_button = PushButton("全选地区")
        self.clear_regions_button = PushButton("取消全选")
        self.refresh_config_button = PushButton("刷新配置")
        region_panel.addWidget(self.select_all_regions_button)
        region_panel.addWidget(self.clear_regions_button)
        region_panel.addWidget(self.refresh_config_button)
        self.region_container_layout = QVBoxLayout()
        region_panel.addLayout(self.region_container_layout)
        self._load_region_checkboxes()
        region_panel.addStretch(1)

        keyword_panel = QVBoxLayout()
        keyword_panel.addWidget(BodyLabel("行业关键词"))
        self.keyword_input = PlainTextEdit()
        self.keyword_input.setPlaceholderText("一行一个关键词，例如：\nCar Wrap Shop\nPPF")
        self.keyword_input.setMinimumHeight(180)
        self.keyword_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        keyword_panel.addWidget(self.keyword_input)
        self.estimated_count_label = BodyLabel("预计生成任务数：0")
        self.preview_button = PrimaryPushButton("生成任务预览")
        self.clear_keywords_button = PushButton("清空关键词")
        keyword_panel.addWidget(self.estimated_count_label)
        keyword_panel.addWidget(self.preview_button)
        keyword_panel.addWidget(self.clear_keywords_button)

        runtime_panel = QVBoxLayout()
        runtime_panel.addWidget(BodyLabel("本次任务参数"))
        self.runtime_relation_label = BodyLabel("本次任务参数从全局默认值初始化；修改后只影响本次任务快照。")
        self.runtime_relation_label.setWordWrap(True)
        runtime_panel.addWidget(self.runtime_relation_label)

        self.browser_combo = ComboBox()
        self.browser_combo.addItems([browser.title() for browser in self.app_config.browser.supported_browsers])
        self.browser_combo.setCurrentText(self.app_config.browser.default_browser.title())
        self.engine_combo = ComboBox()
        self.engine_combo.addItems([engine.title() for engine in self.app_config.browser.supported_engines])
        self.engine_combo.setCurrentText(self.app_config.browser.default_engine.title())
        runtime_panel.addWidget(BodyLabel("浏览器"))
        runtime_panel.addWidget(self.browser_combo)
        runtime_panel.addWidget(BodyLabel("自动化引擎"))
        runtime_panel.addWidget(self.engine_combo)
        self.page_initial_wait_spin = self._add_runtime_spin(
            runtime_panel,
            "页面初始停留秒数",
            0,
            300,
            self.app_config.crawler.page_initial_wait_seconds,
        )
        self.keyword_wait_min_spin = self._add_runtime_spin(
            runtime_panel,
            "关键词停留最小秒数",
            0,
            600,
            self.app_config.crawler.keyword_wait_seconds_min,
        )
        self.keyword_wait_max_spin = self._add_runtime_spin(
            runtime_panel,
            "关键词停留最大秒数",
            0,
            600,
            self.app_config.crawler.keyword_wait_seconds_max,
        )
        self.scroll_wait_min_spin = self._add_runtime_spin(
            runtime_panel,
            "滚动停留最小秒数",
            0,
            120,
            self.app_config.crawler.scroll_wait_seconds_min,
        )
        self.scroll_wait_max_spin = self._add_runtime_spin(
            runtime_panel,
            "滚动停留最大秒数",
            0,
            120,
            self.app_config.crawler.scroll_wait_seconds_max,
        )
        self.max_scroll_rounds_spin = self._add_runtime_spin(
            runtime_panel,
            "最大滚动次数",
            1,
            500,
            self.app_config.crawler.max_scroll_rounds,
        )
        self.no_new_results_spin = self._add_runtime_spin(
            runtime_panel,
            "连续无新增停止次数",
            1,
            50,
            self.app_config.crawler.max_no_new_results_rounds,
        )
        self.page_timeout_spin = self._add_runtime_spin(
            runtime_panel,
            "页面加载超时秒数",
            5,
            600,
            self.app_config.crawler.page_load_timeout_seconds,
        )
        self.failure_threshold_spin = self._add_runtime_spin(
            runtime_panel,
            "连续失败暂停阈值",
            1,
            100,
            self.app_config.crawler.consecutive_failure_pause_threshold,
        )
        self.save_config_button = PrimaryPushButton("保存配置")
        self.restore_default_button = PushButton("恢复默认配置")
        runtime_panel.addWidget(self.save_config_button)
        runtime_panel.addWidget(self.restore_default_button)
        runtime_panel.addStretch(1)

        content_layout.addLayout(region_panel, 2)
        content_layout.addLayout(keyword_panel, 3)
        content_layout.addLayout(runtime_panel, 2)
        content_root_layout.addLayout(content_layout)

        self.preview_table = QTableWidget(0, 6)
        self.preview_table.setHorizontalHeaderLabels(["序号", "行业关键词", "城市", "地区", "国家", "Google Maps 链接"])
        self.preview_table.setItem(0, 0, QTableWidgetItem(""))
        apply_mixed_table_resize(
            self.preview_table,
            stretch_columns={5},
            column_widths={
                0: 70,
                1: 200,
                2: 160,
                3: 180,
                4: 140,
            },
            default_width=140,
        )
        self.preview_table.setMinimumHeight(220)
        self.preview_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_root_layout.addWidget(BodyLabel("任务预览"))
        content_root_layout.addWidget(self.preview_table)

        action_layout = build_action_bar(root_layout)
        self.create_task_button = PrimaryPushButton("创建任务并进入执行页")
        action_layout.addStretch(1)
        action_layout.addWidget(self.create_task_button)

    def selected_country(self):
        """返回当前选择的国家配置。"""
        current_name = self.country_combo.currentText()
        for country in self.locations_config.countries:
            if country.name == current_name:
                return country
        return self.locations_config.countries[0]

    def selected_region_names(self) -> set[str]:
        """返回已选择地区名称。"""
        return {name for name, checkbox in self.region_checkboxes.items() if checkbox.isChecked()}

    def industry_keywords(self) -> list[str]:
        """返回用户输入的行业关键词。"""
        return [line.strip() for line in self.keyword_input.toPlainText().splitlines() if line.strip()]

    def select_all_regions(self) -> None:
        """选择当前国家下全部地区。"""
        for checkbox in self.region_checkboxes.values():
            checkbox.setChecked(True)
        self.update_estimated_count()

    def clear_regions(self) -> None:
        """清空当前国家下全部地区选择。"""
        for checkbox in self.region_checkboxes.values():
            checkbox.setChecked(False)
        self.update_estimated_count()

    def clear_keywords(self) -> None:
        """清空关键词输入框。"""
        self.keyword_input.clear()
        self.update_estimated_count()

    def generate_preview(self) -> list[KeywordTaskInput]:
        """生成任务预览数据并刷新表格。"""
        self.preview_tasks = build_task_inputs(
            country=self.selected_country(),
            selected_region_names=self.selected_region_names(),
            industry_keywords=self.industry_keywords(),
        )
        self.preview_table.setRowCount(len(self.preview_tasks))
        for row_index, task in enumerate(self.preview_tasks):
            values = [
                str(row_index + 1),
                task.industry_keyword,
                task.city_name,
                task.region_name,
                task.country_name,
                task.search_url,
            ]
            for column_index, value in enumerate(values):
                self.preview_table.setItem(row_index, column_index, QTableWidgetItem(value))
        self.update_estimated_count()
        return self.preview_tasks

    def update_estimated_count(self) -> None:
        """更新预计任务数量。"""
        count = len(
            build_task_inputs(
                country=self.selected_country(),
                selected_region_names=self.selected_region_names(),
                industry_keywords=self.industry_keywords(),
            )
        )
        self.estimated_count_label.setText(f"预计生成任务数：{count}")

    def _add_runtime_spin(
        self,
        layout: QVBoxLayout,
        label: str,
        minimum: int,
        maximum: int,
        value: int,
    ) -> SpinBox:
        """向运行参数区域添加一个数字输入框。

        任务页的控件都保留为实例属性，后续创建任务时可以直接读取当前值并写入任务快照。
        """
        layout.addWidget(BodyLabel(label))
        spin_box = SpinBox()
        spin_box.setRange(minimum, maximum)
        spin_box.setValue(value)
        layout.addWidget(spin_box)
        return spin_box

    def _load_region_checkboxes(self) -> None:
        """加载当前国家下的地区复选框。"""
        while self.region_container_layout.count():
            item = self.region_container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.region_checkboxes.clear()
        country = self.selected_country()
        for region in country.regions:
            checkbox = CheckBox(region.name)
            checkbox.stateChanged.connect(self.update_estimated_count)
            self.region_container_layout.addWidget(checkbox)
            self.region_checkboxes[region.name] = checkbox

    def _connect_signals(self) -> None:
        """连接页面内部按钮事件。"""
        self.country_combo.currentTextChanged.connect(self.reload_regions_for_selected_country)
        self.select_all_regions_button.clicked.connect(self.select_all_regions)
        self.clear_regions_button.clicked.connect(self.clear_regions)
        self.preview_button.clicked.connect(self.generate_preview)
        self.clear_keywords_button.clicked.connect(self.clear_keywords)
        self.keyword_input.textChanged.connect(self.update_estimated_count)

    def reload_regions_for_selected_country(self) -> None:
        """切换国家后重新加载地区列表，并默认选择全部地区。"""
        self._load_region_checkboxes()
        self.select_all_regions()
