from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QSizePolicy, QSplitter, QTableWidget, QTextEdit, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, PrimaryPushButton, PushButton

from gmap_collector.gui.layout_utils import build_adaptive_page
from gmap_collector.gui.table_utils import apply_mixed_table_resize


class TaskRunPage(QWidget):
    """任务执行页。

    负责展示任务状态、关键词队列和运行日志。当前阶段按钮暂不连接真实爬取流程。
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
        for index, label in enumerate(
            ["总关键词数", "已完成", "失败", "待执行", "已采集商家数", "去重后商家数", "连续失败次数", "当前关键词", "当前城市", "当前浏览器引擎"]
        ):
            status_layout.addWidget(BodyLabel(label), index, 0)
            status_layout.addWidget(BodyLabel("-"), index, 1)
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
