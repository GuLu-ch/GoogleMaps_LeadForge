from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QScrollArea

from gmap_collector.app import create_application


def test_settings_page_exposes_global_runtime_controls():
    """设置页应聚合基础全局配置，而不是只展示路径文本。"""
    application, window = create_application()

    settings_page = window.settings_page

    assert settings_page.browser_combo.count() == 2
    assert settings_page.engine_combo.count() == 2
    assert Path(settings_page.database_path_input.text()).parts[-2:] == ("data", "app.sqlite3")
    assert Path(settings_page.export_dir_input.text()).name == "exports"
    assert settings_page.max_scroll_rounds_spin.value() == 30
    assert settings_page.save_settings_button.text() == "保存全局设置"

    window.close()
    application.quit()


def test_task_runtime_controls_are_initialized_from_global_defaults():
    """任务配置页的本次运行参数应从全局默认参数初始化。"""
    application, window = create_application()

    settings_page = window.settings_page
    task_page = window.task_config_page

    assert task_page.browser_combo.currentText() == settings_page.browser_combo.currentText()
    assert task_page.engine_combo.currentText() == settings_page.engine_combo.currentText()
    assert task_page.page_initial_wait_spin.value() == settings_page.page_initial_wait_spin.value()
    assert task_page.keyword_wait_min_spin.value() == settings_page.keyword_wait_min_spin.value()
    assert task_page.keyword_wait_max_spin.value() == settings_page.keyword_wait_max_spin.value()
    assert task_page.scroll_wait_min_spin.value() == settings_page.scroll_wait_min_spin.value()
    assert task_page.scroll_wait_max_spin.value() == settings_page.scroll_wait_max_spin.value()
    assert task_page.max_scroll_rounds_spin.value() == settings_page.max_scroll_rounds_spin.value()
    assert task_page.no_new_results_spin.value() == settings_page.no_new_results_spin.value()
    assert task_page.page_timeout_spin.value() == settings_page.page_timeout_spin.value()
    assert task_page.failure_threshold_spin.value() == settings_page.failure_threshold_spin.value()
    assert task_page.runtime_relation_label.text().startswith("本次任务参数")

    window.close()
    application.quit()


def test_tables_use_interactive_columns_and_scrollbars():
    """主要表格应提供可拖拽列宽和滚动条，避免内容被固定窄列挤压。"""
    application, window = create_application()

    preview_header = window.task_config_page.preview_table.horizontalHeader()
    result_header = window.result_page.result_table.horizontalHeader()

    assert preview_header.sectionResizeMode(0) == QHeaderView.Interactive
    assert preview_header.sectionResizeMode(5) == QHeaderView.Stretch
    assert preview_header.defaultSectionSize() >= 120
    assert window.task_config_page.preview_table.columnWidth(1) >= 180
    assert window.task_config_page.preview_table.columnWidth(2) >= 150
    assert window.task_config_page.preview_table.horizontalScrollBarPolicy() == Qt.ScrollBarAsNeeded
    assert window.task_config_page.preview_table.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded
    assert window.task_config_page.preview_table.horizontalScrollMode() == QAbstractItemView.ScrollPerPixel

    assert result_header.sectionResizeMode(0) == QHeaderView.Interactive
    assert result_header.sectionResizeMode(7) == QHeaderView.Stretch
    assert window.result_page.result_table.columnWidth(0) >= 180
    assert window.result_page.result_table.columnWidth(1) >= 240

    window.close()
    application.quit()


def test_main_window_and_pages_support_adaptive_layout():
    """主窗口和主要页面应具备小窗口可滚动的自适应结构。"""
    application, window = create_application()

    assert window.minimumWidth() >= 1100
    assert window.minimumHeight() >= 720

    for page in [
        window.task_config_page,
        window.task_run_page,
        window.result_page,
        window.settings_page,
    ]:
        scroll_area = page.findChild(QScrollArea, "pageScrollArea")
        assert scroll_area is not None
        assert scroll_area.widgetResizable()
        assert scroll_area.horizontalScrollBarPolicy() == Qt.ScrollBarAsNeeded
        assert scroll_area.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded

    assert window.task_config_page.create_task_button.parent() is window.task_config_page
    assert window.settings_page.save_settings_button.parent() is window.settings_page

    window.close()
    application.quit()
