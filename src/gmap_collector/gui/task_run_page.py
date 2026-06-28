from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QTableWidgetItem, QTextEdit, QWidget
from qfluentwidgets import BodyLabel, ComboBox, IndeterminateProgressBar, PrimaryPushButton, PushButton, TableWidget

from gmap_collector.gui.fluent_components import MetricCard, create_button_row, create_section_card, create_text_pair
from gmap_collector.gui.layout_utils import build_adaptive_page
from gmap_collector.gui.table_utils import apply_mixed_table_resize


class TaskRunPage(QWidget):
    """任务执行页。

    负责展示任务状态、关键词队列和运行日志。按钮动作由主窗口统一连接到任务仓储和
    后台执行线程。
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("taskRunPage")
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout, _, content_root_layout = build_adaptive_page(self)

        status_card, status_layout = create_section_card(
            "任务运行状态",
            "展示当前批次、浏览器引擎、正在处理的关键词和实时采集统计。",
        )
        self.running_progress = IndeterminateProgressBar(start=False)
        self.running_progress.setVisible(False)
        status_layout.addWidget(self.running_progress)

        selector_row = QWidget()
        selector_layout = QHBoxLayout(selector_row)
        selector_layout.setContentsMargins(0, 0, 0, 0)
        selector_layout.setSpacing(10)
        selector_label = BodyLabel("当前任务")
        selector_label.setFixedWidth(86)
        self.task_batch_combo = ComboBox()
        self.task_batch_combo.setMinimumWidth(360)
        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self.task_batch_combo, 1)
        status_layout.addWidget(selector_row)

        metric_widget = QWidget()
        metric_layout = QGridLayout(metric_widget)
        metric_layout.setContentsMargins(0, 0, 0, 0)
        metric_layout.setHorizontalSpacing(10)
        metric_layout.setVerticalSpacing(10)
        self.status_labels = {}
        metric_titles = [
            "运行状态",
            "总关键词数",
            "已完成",
            "失败",
            "待执行",
            "已采集商家数",
            "去重后商家数",
            "连续失败次数",
        ]
        for index, title in enumerate(metric_titles):
            card = MetricCard(title)
            metric_layout.addWidget(card, index // 4, index % 4)
            self.status_labels[title] = card.value_label
        status_layout.addWidget(metric_widget)

        context_widget = QWidget()
        context_layout = QGridLayout(context_widget)
        context_layout.setContentsMargins(0, 2, 0, 0)
        context_layout.setHorizontalSpacing(14)
        context_layout.setVerticalSpacing(8)
        context_titles = ["当前关键词", "当前国家", "当前地区", "当前城市", "当前浏览器引擎"]
        for index, title in enumerate(context_titles):
            row_widget, value_label = create_text_pair(title)
            context_layout.addWidget(row_widget, index // 2, index % 2)
            self.status_labels[title] = value_label
        status_layout.addWidget(context_widget)
        content_root_layout.addWidget(status_card)

        queue_card, queue_layout = create_section_card("关键词队列", "显示当前批次中每个关键词的处理状态。")
        self.keyword_table = TableWidget()
        self.keyword_table.setColumnCount(7)
        self.keyword_table.setRowCount(0)
        self.keyword_table.setHorizontalHeaderLabels(["状态", "行业关键词", "城市", "地区", "国家", "失败原因", "最后执行时间"])
        self.keyword_table.setBorderVisible(True)
        self.keyword_table.setBorderRadius(8)
        apply_mixed_table_resize(
            self.keyword_table,
            stretch_columns={5},
            column_widths={
                0: 100,
                1: 220,
                2: 170,
                3: 190,
                4: 150,
                6: 180,
            },
            default_width=150,
        )
        self.keyword_table.setMinimumHeight(300)
        queue_layout.addWidget(self.keyword_table)
        content_root_layout.addWidget(queue_card)

        log_card, log_layout = create_section_card("运行日志")
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(190)
        log_layout.addWidget(self.log_view)
        content_root_layout.addWidget(log_card)

        self.start_button = PrimaryPushButton("开始")
        self.pause_button = PushButton("暂停")
        self.resume_button = PushButton("继续")
        self.stop_button = PushButton("停止")
        self.retry_failed_button = PushButton("重试失败关键词")
        self.export_button = PushButton("导出结果")
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        root_layout.addWidget(
            create_button_row(
                self.start_button,
                self.pause_button,
                self.resume_button,
                self.stop_button,
                self.retry_failed_button,
                self.export_button,
            )
        )

    def load_task_batches(self, batches: list[dict], selected_batch_id: int | None = None) -> None:
        """加载可执行的任务批次下拉框。"""
        current_batch_id = selected_batch_id if selected_batch_id is not None else self.selected_task_batch_id()
        with QSignalBlocker(self.task_batch_combo):
            self.task_batch_combo.clear()
            for batch in batches:
                self.task_batch_combo.addItem(self._task_batch_label(batch), userData=int(batch["id"]))
            if current_batch_id is not None:
                self.select_task_batch(current_batch_id)

    def selected_task_batch_id(self) -> int | None:
        """返回任务执行页当前选择的任务批次 ID。"""
        current_data = self.task_batch_combo.currentData()
        return int(current_data) if current_data is not None else None

    def select_task_batch(self, batch_id: int) -> bool:
        """按批次 ID 选中任务执行页的任务下拉项。"""
        for index in range(self.task_batch_combo.count()):
            if self.task_batch_combo.itemData(index) == batch_id:
                self.task_batch_combo.setCurrentIndex(index)
                return True
        return False

    def load_tasks(
        self,
        batch: dict,
        tasks: list[dict],
        runtime_config: dict | None = None,
        business_stats: dict | None = None,
        consecutive_failures: int = 0,
    ) -> None:
        """加载批次统计和关键词任务表格。"""
        pending_count = sum(1 for task in tasks if task["status"] == "pending")
        current_task = self._current_task(tasks)
        business_stats = business_stats or {"raw_hits": 0, "deduped_businesses": 0}

        status = str(batch.get("status", ""))
        self.status_labels["运行状态"].setText(self._status_text(status))
        self.status_labels["总关键词数"].setText(str(batch["total_keywords"]))
        self.status_labels["已完成"].setText(str(batch["completed_keywords"]))
        self.status_labels["失败"].setText(str(batch["failed_keywords"]))
        self.status_labels["待执行"].setText(str(pending_count))
        self.status_labels["已采集商家数"].setText(str(business_stats.get("raw_hits", 0)))
        self.status_labels["去重后商家数"].setText(str(business_stats.get("deduped_businesses", 0)))
        self.status_labels["连续失败次数"].setText(str(consecutive_failures))
        self.status_labels["当前关键词"].setText(str(current_task.get("keyword", "-")))
        self.status_labels["当前国家"].setText(str(current_task.get("country_name", "-")))
        self.status_labels["当前地区"].setText(str(current_task.get("region_name", "-")))
        self.status_labels["当前城市"].setText(str(current_task.get("city_name", "-")))
        self.status_labels["当前浏览器引擎"].setText(self._engine_text(runtime_config or {}))
        self._set_progress_running(status in {"running"})

        self.keyword_table.setRowCount(len(tasks))
        for row_index, task in enumerate(tasks):
            values = [
                task["status"],
                task["keyword"],
                task["city_name"],
                task["region_name"],
                task["country_name"],
                task["failure_reason"],
                task["last_run_at"] or "",
            ]
            for column_index, value in enumerate(values):
                self.keyword_table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

    def append_log(self, message: str) -> None:
        """追加运行日志。"""
        self.log_view.append(message)

    def show_starting_state(self, runtime_config: dict, task: dict | None, business_stats: dict | None = None) -> None:
        """立即展示启动状态，避免浏览器启动期间界面没有反馈。"""
        task = task or {}
        business_stats = business_stats or {"raw_hits": 0, "deduped_businesses": 0}
        self.status_labels["运行状态"].setText("启动中")
        self.status_labels["当前浏览器引擎"].setText(self._engine_text(runtime_config))
        self.status_labels["当前关键词"].setText(str(task.get("keyword", "-")))
        self.status_labels["当前国家"].setText(str(task.get("country_name", "-")))
        self.status_labels["当前地区"].setText(str(task.get("region_name", "-")))
        self.status_labels["当前城市"].setText(str(task.get("city_name", "-")))
        self.status_labels["已采集商家数"].setText(str(business_stats.get("raw_hits", 0)))
        self.status_labels["去重后商家数"].setText(str(business_stats.get("deduped_businesses", 0)))
        self.set_running(True)

    def set_running(self, running: bool) -> None:
        """根据后台线程状态锁定执行控件，避免用户切换正在运行的任务。"""
        self._set_progress_running(running)
        self.task_batch_combo.setEnabled(not running)
        self.start_button.setEnabled(not running)
        self.resume_button.setEnabled(not running)
        self.retry_failed_button.setEnabled(not running)
        self.export_button.setEnabled(not running)
        self.pause_button.setEnabled(running)
        self.stop_button.setEnabled(running)

    def _current_task(self, tasks: list[dict]) -> dict:
        """优先返回正在执行的任务，其次返回下一条待执行任务。"""
        for status in ["running", "pending", "failed"]:
            for task in tasks:
                if task.get("status") == status:
                    return task
        return {}

    def _engine_text(self, runtime_config: dict) -> str:
        """格式化当前浏览器和自动化引擎。"""
        engine_name = str(runtime_config.get("engine_name", "-")).title()
        browser_name = str(runtime_config.get("browser_name", "-")).title()
        return f"{engine_name} / {browser_name}"

    def _task_batch_label(self, batch: dict) -> str:
        """格式化任务执行页的任务下拉框文本。"""
        return (
            f"#{batch['id']} {batch['name']} | "
            f"{self._status_text(batch['status'])} | "
            f"{batch['completed_keywords']}/{batch['total_keywords']} 完成"
        )

    def _status_text(self, status: str) -> str:
        """将数据库状态转换为界面显示文本。"""
        return {
            "pending": "待执行",
            "running": "运行中",
            "paused": "已暂停",
            "stopped": "已停止",
            "completed": "已完成",
            "completed_with_errors": "已完成，有失败",
        }.get(status, status or "-")

    def _set_progress_running(self, running: bool) -> None:
        """根据任务状态显示或隐藏不确定进度条。"""
        self.running_progress.setVisible(running)
        if running:
            self.running_progress.start()
        else:
            self.running_progress.stop()
