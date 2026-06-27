from PySide6.QtWidgets import QSizePolicy, QTableWidgetItem, QTextEdit, QWidget
from qfluentwidgets import PrimaryPushButton, PushButton, SearchLineEdit, TableWidget

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
            "按关键词、地区、城市或商家分类快速定位已去重的商家记录。",
        )
        self.keyword_filter = SearchLineEdit()
        self.keyword_filter.setPlaceholderText("搜索关键词")
        self.region_filter = SearchLineEdit()
        self.region_filter.setPlaceholderText("搜索地区 / 城市 / 分类")
        self.refresh_button = PushButton("刷新数据")
        self.export_csv_button = PrimaryPushButton("导出 CSV")
        self.export_excel_button = PrimaryPushButton("导出 Excel")
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
        self.result_table.setColumnCount(11)
        self.result_table.setRowCount(0)
        self.result_table.setHorizontalHeaderLabels(
            [
                "商家名称",
                "地址",
                "电话",
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
            stretch_columns={7},
            column_widths={
                0: 200,
                1: 280,
                2: 150,
                3: 220,
                4: 80,
                5: 110,
                6: 160,
                8: 180,
                9: 180,
                10: 180,
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
