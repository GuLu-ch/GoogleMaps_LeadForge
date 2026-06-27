from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QScrollArea

from gmap_collector.app import create_application
from gmap_collector.config.schemas import CityConfig, CountryConfig, LocationsConfig, RegionConfig
from gmap_collector.gui.task_config_page import TaskConfigPage
from gmap_collector.storage.task_repository import KeywordTaskCreate


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


def test_main_window_creates_batch_with_runtime_config_snapshot():
    """从 GUI 创建任务时，应把本次运行参数保存到任务批次快照中。"""
    application, window = create_application()

    window.task_config_page.clear_regions()
    first_checkbox = next(iter(window.task_config_page.region_checkboxes.values()))
    first_checkbox.setChecked(True)
    window.task_config_page.keyword_input.setPlainText("Car Wrap Shop")
    window.task_config_page.max_scroll_rounds_spin.setValue(7)
    window.task_config_page.scroll_wait_min_spin.setValue(2)
    window.task_config_page.scroll_wait_max_spin.setValue(5)
    window.create_task_batch_from_preview()

    batch = window.task_repository.get_batch(window.current_batch_id)

    assert batch["runtime_config"]["browser_name"] == "chrome"
    assert batch["runtime_config"]["max_scroll_rounds"] == 7
    assert batch["runtime_config"]["scroll_wait_seconds_min"] == 2
    assert batch["runtime_config"]["scroll_wait_seconds_max"] == 5

    window.close()
    application.quit()


def test_main_window_retries_failed_tasks_from_task_run_page():
    """任务执行页的重试按钮应能把失败关键词还原为待执行。"""
    application, window = create_application()
    batch_id = window.task_repository.create_batch("测试批次")
    window.task_repository.add_keyword_tasks(
        batch_id,
        [
            KeywordTaskCreate(
                keyword="Car Wrap Shop",
                country_name="德国",
                country_search_name="Germany",
                region_name="柏林州",
                region_search_name="Berlin",
                city_name="柏林",
                city_search_name="Berlin",
                query_text="Car Wrap Shop in Berlin, Berlin, Germany",
                search_url="https://www.google.com/maps/search/Car+Wrap+Shop+in+Berlin",
            )
        ],
    )
    task = window.task_repository.list_keyword_tasks(batch_id)[0]
    window.task_repository.mark_task_failed(task["id"], "页面加载失败")
    window.current_batch_id = batch_id

    window.retry_failed_tasks()

    tasks = window.task_repository.list_keyword_tasks(batch_id)
    assert tasks[0]["status"] == "pending"
    assert tasks[0]["failure_reason"] == ""

    window.close()
    application.quit()


def test_task_config_page_reload_regions_when_country_changes():
    """国家切换后，地区复选框应从新国家配置重新加载。"""
    application, window = create_application()
    locations_config = LocationsConfig(
        countries=(
            CountryConfig(
                name="德国",
                search_name="Germany",
                regions=(
                    RegionConfig(
                        name="柏林州",
                        search_name="Berlin",
                        cities=(CityConfig(name="柏林", search_name="Berlin"),),
                    ),
                ),
            ),
            CountryConfig(
                name="法国",
                search_name="France",
                regions=(
                    RegionConfig(
                        name="法兰西岛",
                        search_name="Ile-de-France",
                        cities=(CityConfig(name="巴黎", search_name="Paris"),),
                    ),
                ),
            ),
        )
    )
    page = TaskConfigPage(app_config=window.app_config, locations_config=locations_config)

    page.country_combo.setCurrentText("法国")

    assert set(page.region_checkboxes) == {"法兰西岛"}
    assert page.selected_region_names() == {"法兰西岛"}

    page.close()
    window.close()
    application.quit()
