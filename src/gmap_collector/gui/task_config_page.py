from PySide6.QtWidgets import QHBoxLayout, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, CheckBox, ComboBox, LineEdit, PlainTextEdit, PrimaryPushButton, PushButton, SpinBox


class TaskConfigPage(QWidget):
    """任务配置页。

    该页面负责地区选择、关键词输入、运行参数配置和任务预览。当前阶段只搭建静态界面，
    后续任务服务实现后再连接按钮事件。
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("taskConfigPage")
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        content_layout = QHBoxLayout()

        region_panel = QVBoxLayout()
        region_panel.addWidget(BodyLabel("国家和地区"))
        self.country_combo = ComboBox()
        self.country_combo.addItem("德国")
        region_panel.addWidget(self.country_combo)
        self.select_all_regions_button = PushButton("全选地区")
        self.clear_regions_button = PushButton("取消全选")
        self.refresh_config_button = PushButton("刷新配置")
        region_panel.addWidget(self.select_all_regions_button)
        region_panel.addWidget(self.clear_regions_button)
        region_panel.addWidget(self.refresh_config_button)
        for region_name in ["巴登-符腾堡州", "巴伐利亚州", "柏林州", "勃兰登堡州"]:
            region_panel.addWidget(CheckBox(region_name))
        region_panel.addStretch(1)

        keyword_panel = QVBoxLayout()
        keyword_panel.addWidget(BodyLabel("行业关键词"))
        self.keyword_input = PlainTextEdit()
        self.keyword_input.setPlaceholderText("一行一个关键词，例如：\nCar Wrap Shop\nPPF")
        keyword_panel.addWidget(self.keyword_input)
        self.estimated_count_label = BodyLabel("预计生成任务数：0")
        self.preview_button = PrimaryPushButton("生成任务预览")
        self.clear_keywords_button = PushButton("清空关键词")
        keyword_panel.addWidget(self.estimated_count_label)
        keyword_panel.addWidget(self.preview_button)
        keyword_panel.addWidget(self.clear_keywords_button)

        runtime_panel = QVBoxLayout()
        runtime_panel.addWidget(BodyLabel("运行参数"))
        self.browser_combo = ComboBox()
        self.browser_combo.addItems(["Chrome", "Edge"])
        self.engine_combo = ComboBox()
        self.engine_combo.addItems(["Selenium", "Playwright"])
        runtime_panel.addWidget(BodyLabel("浏览器"))
        runtime_panel.addWidget(self.browser_combo)
        runtime_panel.addWidget(BodyLabel("自动化引擎"))
        runtime_panel.addWidget(self.engine_combo)
        for label, value in [
            ("页面初始停留秒数", 5),
            ("最大滚动次数", 30),
            ("连续无新增停止次数", 3),
            ("连续失败暂停阈值", 3),
        ]:
            runtime_panel.addWidget(BodyLabel(label))
            spin_box = SpinBox()
            spin_box.setValue(value)
            runtime_panel.addWidget(spin_box)
        self.save_config_button = PrimaryPushButton("保存配置")
        self.restore_default_button = PushButton("恢复默认配置")
        runtime_panel.addWidget(self.save_config_button)
        runtime_panel.addWidget(self.restore_default_button)
        runtime_panel.addStretch(1)

        content_layout.addLayout(region_panel, 2)
        content_layout.addLayout(keyword_panel, 3)
        content_layout.addLayout(runtime_panel, 2)
        root_layout.addLayout(content_layout)

        self.preview_table = QTableWidget(0, 6)
        self.preview_table.setHorizontalHeaderLabels(["序号", "行业关键词", "城市", "地区", "国家", "Google Maps 链接"])
        self.preview_table.setItem(0, 0, QTableWidgetItem(""))
        root_layout.addWidget(BodyLabel("任务预览"))
        root_layout.addWidget(self.preview_table)
        self.create_task_button = PrimaryPushButton("创建任务并进入执行页")
        root_layout.addWidget(self.create_task_button)
