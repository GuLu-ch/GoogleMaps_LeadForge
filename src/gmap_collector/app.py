from PySide6.QtWidgets import QApplication

from gmap_collector.gui.main_window import MainWindow


def create_application() -> tuple[QApplication, MainWindow]:
    """创建 Qt 应用和主窗口。

    返回应用对象和窗口对象，便于命令行入口在 `--check` 模式下只验证初始化。
    """
    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    return application, window
