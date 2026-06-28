from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QTableWidgetItem, QTextEdit, QWidget
from qfluentwidgets import ComboBox, PrimaryPushButton, PushButton, TableWidget

from gmap_collector.gui.fluent_components import create_button_row, create_labeled_spin, create_section_card
from gmap_collector.gui.layout_utils import build_adaptive_page
from gmap_collector.gui.table_utils import apply_mixed_table_resize


class WebsiteExplorationPage(QWidget):
    """官网探索页。

    第一阶段只负责从 Google Maps 任务批次创建官网探索批次，并展示探索任务队列。
    真实网站访问、正则提取和浏览器兜底会在后续模块接入。
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("websiteExplorationPage")
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout, _, content_root_layout = build_adaptive_page(self)

        source_card, source_layout = create_section_card(
            "来源任务",
            "选择某一次 Google Maps 采集任务，把该任务命中的有官网商家放入官网探索队列。",
        )
        self.source_batch_combo = ComboBox()
        self.source_batch_combo.setMinimumWidth(320)
        self.refresh_source_batches_button = PushButton("刷新来源任务")
        source_row = QWidget()
        source_row_layout = QHBoxLayout(source_row)
        source_row_layout.setContentsMargins(0, 0, 0, 0)
        source_row_layout.setSpacing(10)
        source_row_layout.addWidget(self.source_batch_combo, 1)
        source_row_layout.addWidget(self.refresh_source_batches_button)
        source_layout.addWidget(source_row)

        depth_row, self.max_depth_spin = create_labeled_spin("探索深度", 0, 5, 1)
        source_layout.addWidget(depth_row)
        self.create_batch_button = PrimaryPushButton("创建官网探索任务")
        source_layout.addWidget(create_button_row(self.create_batch_button))
        content_root_layout.addWidget(source_card)

        batch_card, batch_layout = create_section_card("探索批次", "展示已经创建的官网探索批次及其统计。")
        self.batch_table = TableWidget()
        self.batch_table.setColumnCount(8)
        self.batch_table.setRowCount(0)
        self.batch_table.setHorizontalHeaderLabels(
            ["批次 ID", "来源任务", "状态", "总商家", "完成", "失败", "跳过", "创建时间"]
        )
        self.batch_table.setBorderVisible(True)
        self.batch_table.setBorderRadius(8)
        apply_mixed_table_resize(
            self.batch_table,
            stretch_columns={7},
            column_widths={
                0: 90,
                1: 100,
                2: 120,
                3: 100,
                4: 90,
                5: 90,
                6: 90,
            },
            default_width=120,
        )
        self.batch_table.setMinimumHeight(220)
        self.batch_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        batch_layout.addWidget(self.batch_table)
        content_root_layout.addWidget(batch_card)

        task_card, task_layout = create_section_card("探索任务", "展示当前探索批次中的商家官网处理状态。")
        self.task_table = TableWidget()
        self.task_table.setColumnCount(6)
        self.task_table.setRowCount(0)
        self.task_table.setHorizontalHeaderLabels(["状态", "商家名称", "官网", "失败原因", "最后执行时间", "商家 ID"])
        self.task_table.setBorderVisible(True)
        self.task_table.setBorderRadius(8)
        apply_mixed_table_resize(
            self.task_table,
            stretch_columns={2},
            column_widths={
                0: 110,
                1: 220,
                3: 180,
                4: 180,
                5: 90,
            },
            default_width=150,
        )
        self.task_table.setMinimumHeight(260)
        self.task_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        task_layout.addWidget(self.task_table)
        content_root_layout.addWidget(task_card)

        log_card, log_layout = create_section_card("探索日志")
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(150)
        log_layout.addWidget(self.log_view)
        content_root_layout.addWidget(log_card)

        self.start_button = PrimaryPushButton("开始探索")
        self.pause_button = PushButton("暂停")
        self.stop_button = PushButton("停止")
        self.export_button = PushButton("导出探索结果")
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.export_button.setEnabled(False)
        root_layout.addWidget(
            create_button_row(
                self.start_button,
                self.pause_button,
                self.stop_button,
                self.export_button,
            )
        )

    def load_source_batches(self, batches: list[dict]) -> None:
        """加载可作为官网探索来源的 Google Maps 批次。"""
        current_batch_id = self.selected_source_batch_id()
        self.source_batch_combo.clear()
        for batch in batches:
            label = self._source_batch_label(batch)
            self.source_batch_combo.addItem(label, userData=int(batch["id"]))
        if current_batch_id is not None:
            for index in range(self.source_batch_combo.count()):
                if self.source_batch_combo.itemData(index) == current_batch_id:
                    self.source_batch_combo.setCurrentIndex(index)
                    break

    def selected_source_batch_id(self) -> int | None:
        """返回当前选择的 Google Maps 来源批次 ID。"""
        current_data = self.source_batch_combo.currentData()
        return int(current_data) if current_data is not None else None

    def exploration_runtime_config(self) -> dict[str, int]:
        """读取官网探索任务运行参数快照。"""
        return {"max_depth": self.max_depth_spin.value()}

    def load_exploration_batches(self, batches: list[dict]) -> None:
        """加载官网探索批次表格。"""
        self.batch_table.setRowCount(len(batches))
        for row_index, batch in enumerate(batches):
            values = [
                batch["id"],
                batch["source_batch_id"],
                self._status_text(batch["status"]),
                batch["total_businesses"],
                batch["completed_businesses"],
                batch["failed_businesses"],
                batch["skipped_businesses"],
                batch["created_at"],
            ]
            for column_index, value in enumerate(values):
                self.batch_table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

    def load_tasks(self, tasks: list[dict]) -> None:
        """加载当前官网探索批次的任务队列。"""
        self.task_table.setRowCount(len(tasks))
        for row_index, task in enumerate(tasks):
            values = [
                self._status_text(task["status"]),
                task["business_name"],
                task["website_url"],
                task["failure_reason"],
                task["last_run_at"] or "",
                task["business_id"],
            ]
            for column_index, value in enumerate(values):
                self.task_table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

    def append_log(self, message: str) -> None:
        """追加官网探索日志。"""
        self.log_view.append(message)

    def _source_batch_label(self, batch: dict) -> str:
        """格式化来源 Google Maps 批次下拉框文本。"""
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
            "success": "完成",
            "failed": "失败",
            "skipped": "跳过",
            "completed": "已完成",
            "completed_with_errors": "已完成，有失败",
        }.get(status, status or "-")
