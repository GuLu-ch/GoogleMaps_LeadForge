from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QTableWidget, QTextEdit, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, PrimaryPushButton, PushButton


class TaskRunPage(QWidget):
    """任务执行页。

    负责展示任务状态、关键词队列和运行日志。当前阶段按钮暂不连接真实爬取流程。
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("taskRunPage")
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)

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

        middle_layout = QHBoxLayout()
        status_layout = QGridLayout()
        for index, label in enumerate(
            ["总关键词数", "已完成", "失败", "待执行", "已采集商家数", "去重后商家数", "连续失败次数", "当前关键词", "当前城市", "当前浏览器引擎"]
        ):
            status_layout.addWidget(BodyLabel(label), index, 0)
            status_layout.addWidget(BodyLabel("-"), index, 1)
        middle_layout.addLayout(status_layout, 2)

        self.keyword_table = QTableWidget(0, 7)
        self.keyword_table.setHorizontalHeaderLabels(["状态", "行业关键词", "城市", "地区", "国家", "失败原因", "最后执行时间"])
        middle_layout.addWidget(self.keyword_table, 5)
        root_layout.addLayout(middle_layout)

        root_layout.addWidget(BodyLabel("运行日志"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        root_layout.addWidget(self.log_view)
