from pathlib import Path

from PySide6.QtWidgets import QGridLayout, QWidget
from qfluentwidgets import BodyLabel, PushButton


class SettingsPage(QWidget):
    """设置与文档页。

    当前阶段展示关键目录和文档路径，后续可连接打开目录按钮。
    """

    def __init__(self, project_root: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.project_root = project_root
        self.setObjectName("settingsPage")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QGridLayout(self)
        paths = [
            ("运行配置", "config/app_config.json"),
            ("地区配置", "config/locations.de.json"),
            ("SQLite 数据库", "data/app.sqlite3"),
            ("导出目录", "exports"),
            ("日志目录", "logs"),
            ("README", "README.md"),
            ("智能体规范", "AGENTS.md"),
            ("需求文档", "docs/REQUIREMENTS.md"),
            ("设计文档", "docs/DESIGN.md"),
            ("项目结构", "docs/PROJECT_STRUCTURE.md"),
        ]
        for row, (label, relative_path) in enumerate(paths):
            layout.addWidget(BodyLabel(label), row, 0)
            layout.addWidget(BodyLabel(str(self.project_root / relative_path)), row, 1)

        self.open_config_button = PushButton("打开配置目录")
        self.open_export_button = PushButton("打开导出目录")
        self.open_log_button = PushButton("打开日志目录")
        layout.addWidget(self.open_config_button, len(paths), 0)
        layout.addWidget(self.open_export_button, len(paths), 1)
        layout.addWidget(self.open_log_button, len(paths), 2)
