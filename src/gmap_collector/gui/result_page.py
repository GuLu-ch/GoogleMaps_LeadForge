from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QSizePolicy, QTableWidgetItem, QTextEdit, QWidget
from qfluentwidgets import ComboBox, PrimaryPushButton, PushButton, SearchLineEdit, TableWidget

from gmap_collector.gui.fluent_components import create_button_row, create_section_card
from gmap_collector.gui.layout_utils import build_adaptive_page
from gmap_collector.gui.table_utils import apply_mixed_table_resize


class ResultPage(QWidget):
    """结果管理页。

    负责展示去重后的商家记录、筛选条件和导出按钮。
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("resultPage")
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout, _, content_root_layout = build_adaptive_page(self)

        filter_card, filter_layout = create_section_card(
            "结果筛选",
            "以任务为基本单位查看和导出商家结果，并可按关键词、地区、城市或商家分类辅助定位。",
        )
        self.task_batch_combo = ComboBox()
        self.task_batch_combo.setMinimumWidth(320)
        self.keyword_filter = SearchLineEdit()
        self.keyword_filter.setPlaceholderText("搜索关键词")
        self.region_filter = SearchLineEdit()
        self.region_filter.setPlaceholderText("搜索地区 / 城市 / 分类")
        self.refresh_button = PushButton("刷新数据")
        self.export_csv_button = PrimaryPushButton("导出 CSV")
        self.export_excel_button = PrimaryPushButton("导出 Excel")
        filter_layout.addWidget(self.task_batch_combo)
        filter_layout.addWidget(self.keyword_filter)
        filter_layout.addWidget(self.region_filter)
        filter_layout.addWidget(
            create_button_row(
                self.refresh_button,
                self.export_csv_button,
                self.export_excel_button,
            )
        )
        content_root_layout.addWidget(filter_card)

        table_card, table_layout = create_section_card("商家结果", "表格展示全局去重后的商家信息。")
        self.result_table = TableWidget()
        self.result_table.setColumnCount(23)
        self.result_table.setRowCount(0)
        self.result_table.setHorizontalHeaderLabels(
            [
                "商家名称",
                "地址",
                "电话",
                "官网探索电话",
                "Email",
                "Instagram",
                "TikTok",
                "Twitter / X",
                "Facebook",
                "LinkedIn",
                "YouTube",
                "WhatsApp",
                "SEO Keywords",
                "官网探索状态",
                "官网探索时间",
                "官网",
                "评分",
                "评论数量",
                "商家分类",
                "Google Maps 链接",
                "来源关键词",
                "首次采集时间",
                "最后更新时间",
            ]
        )
        self.result_table.setBorderVisible(True)
        self.result_table.setBorderRadius(8)
        apply_mixed_table_resize(
            self.result_table,
            stretch_columns={12, 19},
            column_widths={
                0: 200,
                1: 280,
                2: 150,
                3: 160,
                4: 220,
                5: 180,
                6: 180,
                7: 180,
                8: 180,
                9: 180,
                10: 180,
                11: 180,
                13: 130,
                14: 170,
                15: 220,
                16: 80,
                17: 110,
                18: 160,
                20: 180,
                21: 180,
                22: 180,
            },
            default_width=150,
        )
        self.result_table.setMinimumHeight(360)
        self.result_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table_layout.addWidget(self.result_table)
        content_root_layout.addWidget(table_card)

        detail_card, detail_layout = create_section_card("详情")
        self.detail_view = QTextEdit()
        self.detail_view.setReadOnly(True)
        self.detail_view.setMinimumHeight(160)
        detail_layout.addWidget(self.detail_view)
        content_root_layout.addWidget(detail_card)

    def load_businesses(self, businesses: list[dict]) -> None:
        """加载去重后的商家结果。"""
        self.result_table.setRowCount(len(businesses))
        for row_index, business in enumerate(businesses):
            values = [
                business["name"],
                business["address"],
                business["phone"],
                business["explored_phone"],
                business["emails"],
                business["instagram"],
                business["tiktok"],
                business["twitter_x"],
                business["facebook"],
                business["linkedin"],
                business["youtube"],
                business["whatsapp"],
                business["seo_keywords"],
                business["website_exploration_status"],
                business["website_explored_at"],
                business["website"],
                business["rating"],
                business["review_count"],
                business["category"],
                business["google_maps_url"],
                business["source_keywords"],
                business["first_seen_at"],
                business["last_seen_at"],
            ]
            for column_index, value in enumerate(values):
                self.result_table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

    def load_task_batches(self, batches: list[dict]) -> None:
        """加载可查看结果的任务批次。"""
        current_batch_id = self.selected_task_batch_id()
        with QSignalBlocker(self.task_batch_combo):
            self.task_batch_combo.clear()
            for batch in batches:
                self.task_batch_combo.addItem(self._task_batch_label(batch), userData=int(batch["id"]))
            if current_batch_id is not None:
                self.select_task_batch(current_batch_id)

    def selected_task_batch_id(self) -> int | None:
        """返回当前选择的任务批次 ID。"""
        current_data = self.task_batch_combo.currentData()
        return int(current_data) if current_data is not None else None

    def select_task_batch(self, batch_id: int) -> None:
        """按批次 ID 选择结果任务。"""
        for index in range(self.task_batch_combo.count()):
            if self.task_batch_combo.itemData(index) == batch_id:
                self.task_batch_combo.setCurrentIndex(index)
                return

    def _task_batch_label(self, batch: dict) -> str:
        """格式化结果任务下拉框文本。"""
        return (
            f"#{batch['id']} {batch['name']} | "
            f"{self._status_text(batch['status'])} | "
            f"{batch['completed_keywords']}/{batch['total_keywords']} 完成"
        )

    def _status_text(self, status: str) -> str:
        """将数据库任务状态转为中文。"""
        return {
            "pending": "待执行",
            "running": "运行中",
            "paused": "已暂停",
            "stopped": "已停止",
            "completed": "已完成",
            "completed_with_errors": "已完成，有失败",
        }.get(status, status or "-")
