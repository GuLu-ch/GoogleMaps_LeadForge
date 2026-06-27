from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QSizePolicy, QSplitter, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, PrimaryPushButton, PushButton

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

        control_layout = QHBoxLayout()
        self.start_button = PrimaryPushButton("开始")
        self.pause_button = PushButton("暂停")
        self.resume_button = PushButton("继续")
        self.stop_button = PushButton("停止")
        self.retry_failed_button = PushButton("重试失败关键词")
        self.export_button = PushButton("导出结果")
        for button in [
            self.start_button,
            self.pause_button,
            self.resume_button,
            self.stop_button,
            self.retry_failed_button,
            self.export_button,
        ]:
            control_layout.addWidget(button)
        control_layout.addStretch(1)
        root_layout.addLayout(control_layout)

        middle_splitter = QSplitter(Qt.Horizontal)
        middle_splitter.setChildrenCollapsible(False)
        middle_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        status_widget = QWidget()
        status_layout = QGridLayout()
        status_widget.setLayout(status_layout)
        self.status_labels: dict[str, BodyLabel] = {}
        status_items = [
            "运行状态",
            "总关键词数",
            "已完成",
            "失败",
            "待执行",
            "已采集商家数",
            "去重后商家数",
            "连续失败次数",
            "当前关键词",
            "当前国家",
            "当前地区",
            "当前城市",
            "当前浏览器引擎",
        ]
        for index, label in enumerate(status_items):
            status_layout.addWidget(BodyLabel(label), index, 0)
            value_label = BodyLabel("-")
            value_label.setWordWrap(True)
            status_layout.addWidget(value_label, index, 1)
            self.status_labels[label] = value_label
        status_widget.setMinimumWidth(260)
        middle_splitter.addWidget(status_widget)

        self.keyword_table = QTableWidget(0, 7)
        self.keyword_table.setHorizontalHeaderLabels(["状态", "行业关键词", "城市", "地区", "国家", "失败原因", "最后执行时间"])
        apply_mixed_table_resize(
            self.keyword_table,
            stretch_columns={5},
            column_widths={
                0: 100,
                1: 200,
                2: 160,
                3: 180,
                4: 140,
                6: 180,
            },
            default_width=140,
        )
        self.keyword_table.setMinimumHeight(260)
        middle_splitter.addWidget(self.keyword_table)
        middle_splitter.setStretchFactor(0, 2)
        middle_splitter.setStretchFactor(1, 5)
        content_root_layout.addWidget(middle_splitter)

        content_root_layout.addWidget(BodyLabel("运行日志"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(180)
        content_root_layout.addWidget(self.log_view)

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

        self.status_labels["运行状态"].setText(self._status_text(str(batch.get("status", ""))))
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
