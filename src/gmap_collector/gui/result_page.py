from PySide6.QtWidgets import QHBoxLayout, QTableWidget, QTextEdit, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, LineEdit, PrimaryPushButton, PushButton


class ResultPage(QWidget):
    """结果管理页。

    负责展示去重后的商家记录、筛选条件和导出按钮。
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("resultPage")
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()
        self.keyword_filter = LineEdit()
        self.keyword_filter.setPlaceholderText("关键词")
        self.region_filter = LineEdit()
        self.region_filter.setPlaceholderText("地区/城市/分类")
        self.refresh_button = PushButton("刷新数据")
        self.export_csv_button = PrimaryPushButton("导出 CSV")
        self.export_excel_button = PrimaryPushButton("导出 Excel")
        for widget in [
            self.keyword_filter,
            self.region_filter,
            self.refresh_button,
            self.export_csv_button,
            self.export_excel_button,
        ]:
            filter_layout.addWidget(widget)
        root_layout.addLayout(filter_layout)

        self.result_table = QTableWidget(0, 11)
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
        root_layout.addWidget(self.result_table)

        root_layout.addWidget(BodyLabel("详情"))
        self.detail_view = QTextEdit()
        self.detail_view.setReadOnly(True)
        root_layout.addWidget(self.detail_view)
