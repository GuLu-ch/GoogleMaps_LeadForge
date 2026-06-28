from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QSizePolicy
from qfluentwidgets import IndeterminateProgressBar, NavigationItemPosition, ScrollArea, SettingCardGroup, TableWidget

import gmap_collector.gui.main_window as main_window_module
from gmap_collector.app import create_application
from gmap_collector.config.schemas import CityConfig, CountryConfig, LocationsConfig, RegionConfig
from gmap_collector.common.models import BusinessRecord
from gmap_collector.gui.fluent_components import NoWheelSpinBox
from gmap_collector.gui.task_config_page import TaskConfigPage
from gmap_collector.storage.task_repository import KeywordTaskCreate


def test_settings_page_exposes_global_runtime_controls():
    """设置页应通过 Fluent 设置卡片聚合全局配置。"""
    application, window = create_application()

    settings_page = window.settings_page

    assert isinstance(settings_page.appearance_group, SettingCardGroup)
    assert isinstance(settings_page.runtime_group, SettingCardGroup)
    assert isinstance(settings_page.path_group, SettingCardGroup)
    assert isinstance(settings_page.maintenance_group, SettingCardGroup)
    assert settings_page.theme_combo.currentText() in {"亮色", "暗色", "跟随系统"}
    assert settings_page.browser_combo.count() == 2
    assert settings_page.engine_combo.count() == 2
    assert Path(settings_page.path_cards["SQLite 数据库"].contentLabel.text()).parts[-2:] == ("data", "app.sqlite3")
    assert Path(settings_page.path_cards["导出目录"].contentLabel.text()).name == "exports"
    assert settings_page.max_scroll_rounds_spin.value() == 30
    assert settings_page.save_settings_button.text() == "保存全局设置"
    assert settings_page.clear_runtime_data_button.text() == "清空数据库和缓存"

    window.close()
    application.quit()


def test_settings_page_does_not_show_project_document_group():
    """设置页不应展示项目文档分组，避免把开发文档混入用户配置页面。"""
    application, window = create_application()

    assert not hasattr(window.settings_page, "docs_group")

    window.close()
    application.quit()


def test_settings_page_clear_runtime_data_button_triggers_main_window_cleanup(monkeypatch):
    """设置页清理按钮应调用主窗口的运行数据清理流程。"""
    application, window = create_application()
    called = {"cleanup": False}

    def fake_cleanup():
        called["cleanup"] = True

    monkeypatch.setattr(window, "clear_runtime_data_from_settings", fake_cleanup)
    window.settings_page.clear_runtime_data_button.clicked.emit()

    assert called["cleanup"] is True

    window.close()
    application.quit()


def test_main_window_clear_runtime_data_reinitializes_database(monkeypatch):
    """确认清理后，主窗口应删除运行数据并重新初始化空数据库。"""
    application, window = create_application()
    batch_id = window.task_repository.create_batch("清理测试批次")
    window.current_batch_id = batch_id
    assert window.task_repository.get_batch(batch_id)["id"] == batch_id

    monkeypatch.setattr(window, "_confirm_clear_runtime_data", lambda: True)

    window.clear_runtime_data_from_settings()

    assert window.current_batch_id is None
    assert window.task_repository.get_latest_resumable_batch_id() is None
    assert window.business_repository.get_business_stats() == {"raw_hits": 0, "deduped_businesses": 0}

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


def test_runtime_spin_boxes_ignore_mouse_wheel():
    """运行参数数字框应忽略滚轮，避免滚动页面时误改参数。"""
    application, window = create_application()

    spin_boxes = [
        window.task_config_page.page_initial_wait_spin,
        window.task_config_page.keyword_wait_min_spin,
        window.task_config_page.keyword_wait_max_spin,
        window.task_config_page.scroll_wait_min_spin,
        window.task_config_page.scroll_wait_max_spin,
        window.task_config_page.max_scroll_rounds_spin,
        window.task_config_page.no_new_results_spin,
        window.task_config_page.page_timeout_spin,
        window.task_config_page.failure_threshold_spin,
        window.settings_page.page_initial_wait_spin,
        window.settings_page.keyword_wait_min_spin,
        window.settings_page.keyword_wait_max_spin,
        window.settings_page.scroll_wait_min_spin,
        window.settings_page.scroll_wait_max_spin,
        window.settings_page.max_scroll_rounds_spin,
        window.settings_page.no_new_results_spin,
        window.settings_page.page_timeout_spin,
        window.settings_page.failure_threshold_spin,
    ]

    assert all(isinstance(spin_box, NoWheelSpinBox) for spin_box in spin_boxes)
    assert all(spin_box.focusPolicy() == Qt.StrongFocus for spin_box in spin_boxes)

    window.close()
    application.quit()


def test_tables_use_interactive_columns_and_scrollbars():
    """主要表格应使用 Fluent 表格，并提供可拖拽列宽和滚动条。"""
    application, window = create_application()

    assert isinstance(window.task_config_page.preview_table, TableWidget)
    assert isinstance(window.task_run_page.keyword_table, TableWidget)
    assert isinstance(window.result_page.result_table, TableWidget)

    preview_header = window.task_config_page.preview_table.horizontalHeader()
    result_header = window.result_page.result_table.horizontalHeader()

    assert preview_header.sectionResizeMode(0) == QHeaderView.Interactive
    assert preview_header.sectionResizeMode(5) == QHeaderView.Stretch
    assert preview_header.defaultSectionSize() >= 120
    assert window.task_config_page.preview_table.columnWidth(1) >= 180
    assert window.task_config_page.preview_table.columnWidth(2) >= 150
    assert hasattr(window.task_config_page.preview_table, "scrollDelagate")
    assert not window.task_config_page.preview_table.scrollDelagate.hScrollBar._isForceHidden
    assert not window.task_config_page.preview_table.scrollDelagate.vScrollBar._isForceHidden
    assert window.task_config_page.preview_table.horizontalScrollMode() == QAbstractItemView.ScrollPerPixel

    assert result_header.sectionResizeMode(0) == QHeaderView.Interactive
    assert result_header.sectionResizeMode(12) == QHeaderView.Stretch
    assert result_header.sectionResizeMode(19) == QHeaderView.Stretch
    assert window.result_page.result_table.columnWidth(0) >= 180
    assert window.result_page.result_table.columnWidth(1) >= 240
    assert hasattr(window.result_page.result_table, "scrollDelagate")
    assert not window.result_page.result_table.scrollDelagate.hScrollBar._isForceHidden
    assert not window.result_page.result_table.scrollDelagate.vScrollBar._isForceHidden

    window.close()
    application.quit()


def test_main_window_and_pages_support_adaptive_layout():
    """主窗口和主要页面应具备小窗口可滚动的自适应结构。"""
    application, window = create_application()

    assert window.width() <= 1200
    assert window.height() <= 780
    assert window.minimumWidth() >= 1100
    assert window.minimumHeight() >= 720

    for page in [
        window.task_config_page,
        window.task_run_page,
        window.result_page,
        window.website_exploration_page,
        window.settings_page,
    ]:
        scroll_area = page.findChild(ScrollArea, "pageScrollArea")
        assert scroll_area is not None
        assert scroll_area.widgetResizable()
        assert hasattr(scroll_area, "scrollDelagate")
        assert not scroll_area.scrollDelagate.hScrollBar._isForceHidden
        assert not scroll_area.scrollDelagate.vScrollBar._isForceHidden

    assert window.task_config_page.create_task_button.parent() is window.task_config_page
    assert window.settings_page.save_settings_button.parent() is window.settings_page

    window.close()
    application.quit()


def test_main_window_exposes_website_exploration_page():
    """主窗口应提供独立的官网探索页面入口。"""
    application, window = create_application()

    assert window.website_exploration_page.objectName() == "websiteExplorationPage"
    assert isinstance(window.website_exploration_page.batch_table, TableWidget)
    assert isinstance(window.website_exploration_page.task_table, TableWidget)
    assert window.website_exploration_page.source_batch_combo.count() >= 0

    window.close()
    application.quit()


def test_website_exploration_navigation_is_before_result_page():
    """官网探索应位于结果管理之前，体现二次任务先于最终汇总结果。"""
    application, window = create_application()

    assert window.stackedWidget.indexOf(window.website_exploration_page) < window.stackedWidget.indexOf(window.result_page)

    window.close()
    application.quit()


def test_website_exploration_page_creates_batch_from_selected_maps_task():
    """官网探索页应能从选中的 Google Maps 批次创建探索批次并展示任务列表。"""
    application, window = create_application()
    maps_batch_id = window.task_repository.create_batch("官网探索来源批次")
    window.task_repository.add_keyword_tasks(
        maps_batch_id,
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
    keyword_task = window.task_repository.list_keyword_tasks(maps_batch_id)[0]
    window.business_repository.upsert_business(
        BusinessRecord(
            name="Alpha Wrap",
            address="Street 1",
            phone="+49 111",
            website="https://alpha.example.com",
            rating="4.8",
            review_count="120",
            category="Car wrap shop",
            google_maps_url="https://maps.google.com/?cid=1",
            source_keyword="Car Wrap Shop",
        ),
        keyword_task_id=keyword_task["id"],
        query_text=keyword_task["query_text"],
    )

    window.refresh_website_exploration_page()
    window.website_exploration_page.source_batch_combo.setCurrentIndex(0)
    window.create_website_exploration_batch()

    assert window.current_website_exploration_batch_id is not None
    assert window.website_exploration_page.batch_table.rowCount() >= 1
    assert window.website_exploration_page.task_table.rowCount() == 1
    assert window.website_exploration_page.task_table.item(0, 1).text() == "Alpha Wrap"
    assert window.website_exploration_page.task_table.item(0, 2).text() == "https://alpha.example.com"

    window.close()
    application.quit()


def test_result_page_shows_website_exploration_columns():
    """结果管理应展示官网探索新增字段，作为最终汇总视图。"""
    application, window = create_application()

    headers = [
        window.result_page.result_table.horizontalHeaderItem(index).text()
        for index in range(window.result_page.result_table.columnCount())
    ]

    assert headers[:15] == [
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
    ]
    assert "官网" in headers
    assert "Google Maps 链接" in headers

    window.close()
    application.quit()


def test_settings_navigation_item_is_placed_at_bottom():
    """设置入口应固定在左侧导航底部，和普通业务页面分离。"""
    application, window = create_application()

    setting_item = window.navigationInterface.widget(window.settings_page.objectName())

    assert setting_item is not None
    assert setting_item.property("position") == NavigationItemPosition.BOTTOM

    window.close()
    application.quit()


def test_main_window_uses_compact_navigation_expand_width():
    """左侧导航展开宽度应比组件默认值更紧凑，减少内容区被占用。"""
    application, window = create_application()

    assert window.navigationInterface.panel.expandWidth == 220

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


def test_task_run_page_shows_runtime_context_and_current_task():
    """任务执行页应展示运行状态、当前关键词、国家地区和浏览器引擎。"""
    application, window = create_application()
    batch = {
        "status": "running",
        "total_keywords": 1,
        "completed_keywords": 0,
        "failed_keywords": 0,
    }
    tasks = [
        {
            "status": "running",
            "keyword": "Car Wrap Shop",
            "city_name": "柏林",
            "region_name": "柏林州",
            "country_name": "德国",
            "failure_reason": "",
            "last_run_at": "",
        }
    ]

    window.task_run_page.load_tasks(
        batch=batch,
        tasks=tasks,
        runtime_config={"engine_name": "selenium", "browser_name": "chrome"},
        business_stats={"raw_hits": 3, "deduped_businesses": 2},
        consecutive_failures=1,
    )

    labels = window.task_run_page.status_labels
    assert labels["运行状态"].text() == "运行中"
    assert labels["当前浏览器引擎"].text() == "Selenium / Chrome"
    assert labels["当前关键词"].text() == "Car Wrap Shop"
    assert labels["当前国家"].text() == "德国"
    assert labels["当前地区"].text() == "柏林州"
    assert labels["当前城市"].text() == "柏林"
    assert labels["已采集商家数"].text() == "3"
    assert labels["去重后商家数"].text() == "2"
    assert labels["连续失败次数"].text() == "1"

    window.close()
    application.quit()


def test_task_run_page_shows_starting_state_before_browser_ready():
    """点击开始后，应立即展示启动状态、下一条任务信息和加载进度条。"""
    application, window = create_application()

    assert isinstance(window.task_run_page.running_progress, IndeterminateProgressBar)
    assert window.task_run_page.running_progress.isHidden()

    window.task_run_page.show_starting_state(
        runtime_config={"engine_name": "selenium", "browser_name": "chrome"},
        task={
            "keyword": "PPF",
            "city_name": "慕尼黑",
            "region_name": "巴伐利亚州",
            "country_name": "德国",
        },
        business_stats={"raw_hits": 0, "deduped_businesses": 0},
    )

    labels = window.task_run_page.status_labels
    assert labels["运行状态"].text() == "启动中"
    assert labels["当前浏览器引擎"].text() == "Selenium / Chrome"
    assert labels["当前关键词"].text() == "PPF"
    assert labels["当前国家"].text() == "德国"
    assert labels["当前地区"].text() == "巴伐利亚州"
    assert labels["当前城市"].text() == "慕尼黑"
    assert not window.task_run_page.running_progress.isHidden()

    window.task_run_page.load_tasks(
        batch={
            "status": "completed",
            "total_keywords": 1,
            "completed_keywords": 1,
            "failed_keywords": 0,
        },
        tasks=[],
        runtime_config={"engine_name": "selenium", "browser_name": "chrome"},
    )
    assert window.task_run_page.running_progress.isHidden()

    window.close()
    application.quit()


def test_main_window_shows_starting_state_when_start_clicked(monkeypatch):
    """点击开始后，主窗口应在浏览器真正打开前立即刷新启动状态。"""

    class FakeSignal:
        """测试用信号对象，只记录连接函数。"""

        def __init__(self):
            self.connected = []

        def connect(self, callback):
            self.connected.append(callback)

    class FakeTaskWorker:
        """避免测试中真的启动浏览器的任务线程替身。"""

        def __init__(self, *args, **kwargs):
            self.log_message = FakeSignal()
            self.task_changed = FakeSignal()
            self.finished_summary = FakeSignal()
            self.started = False

        def isRunning(self):
            return False

        def start(self):
            self.started = True

    monkeypatch.setattr(main_window_module, "TaskWorker", FakeTaskWorker)
    application, window = create_application()
    batch_id = window.task_repository.create_batch(
        "启动状态测试",
        runtime_config={
            "browser_name": "chrome",
            "engine_name": "selenium",
            "page_initial_wait_seconds": 0,
            "keyword_wait_seconds_min": 0,
            "keyword_wait_seconds_max": 0,
            "scroll_wait_seconds_min": 0,
            "scroll_wait_seconds_max": 0,
            "max_scroll_rounds": 1,
            "no_new_results_threshold": 1,
            "page_load_timeout_seconds": 30,
            "failure_threshold": 3,
        },
    )
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
    window.current_batch_id = batch_id

    window.start_current_batch()

    labels = window.task_run_page.status_labels
    assert labels["运行状态"].text() == "启动中"
    assert labels["当前浏览器引擎"].text() == "Selenium / Chrome"
    assert labels["当前关键词"].text() == "Car Wrap Shop"
    assert labels["当前国家"].text() == "德国"
    assert labels["当前地区"].text() == "柏林州"
    assert labels["当前城市"].text() == "柏林"
    assert window.task_worker.started is True

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


def test_task_config_regions_are_inside_bounded_scroll_area():
    """地区复选框较多时，应只撑开局部滚动区，不能撑高整个配置页。"""
    application, window = create_application()
    many_regions = tuple(
        RegionConfig(
            name=f"测试地区 {index}",
            search_name=f"Region {index}",
            cities=(CityConfig(name=f"城市 {index}", search_name=f"City {index}"),),
        )
        for index in range(120)
    )
    locations_config = LocationsConfig(
        countries=(
            CountryConfig(
                name="测试国家",
                search_name="Testland",
                regions=many_regions,
            ),
        )
    )

    page = TaskConfigPage(app_config=window.app_config, locations_config=locations_config)

    assert page.region_scroll_area.minimumHeight() >= 320
    assert page.region_scroll_area.sizePolicy().verticalPolicy() == QSizePolicy.Expanding
    assert page.region_scroll_area.widgetResizable()
    assert hasattr(page.region_scroll_area, "scrollDelagate")
    assert not page.region_scroll_area.scrollDelagate.vScrollBar._isForceHidden
    assert page.region_scroll_area.scrollDelagate.hScrollBar._isForceHidden
    assert len(page.region_checkboxes) == 120
    first_checkbox = page.region_checkboxes["测试地区 0"]
    assert page.region_scroll_content.isAncestorOf(first_checkbox)

    page.close()
    window.close()
    application.quit()


def test_task_config_region_rows_keep_normal_height_when_region_count_is_small():
    """地区很少时，复选框行高应保持正常，多余空间由底部弹性区占用。"""
    application, window = create_application()
    locations_config = LocationsConfig(
        countries=(
            CountryConfig(
                name="小国家",
                search_name="Smallland",
                regions=(
                    RegionConfig(
                        name="地区 A",
                        search_name="Region A",
                        cities=(CityConfig(name="城市 A", search_name="City A"),),
                    ),
                    RegionConfig(
                        name="地区 B",
                        search_name="Region B",
                        cities=(CityConfig(name="城市 B", search_name="City B"),),
                    ),
                ),
            ),
        )
    )

    page = TaskConfigPage(app_config=window.app_config, locations_config=locations_config)

    assert page.region_container_layout.count() == 3
    assert page.region_container_layout.itemAt(2).spacerItem() is not None
    for checkbox in page.region_checkboxes.values():
        assert checkbox.maximumHeight() <= 36
        assert checkbox.sizePolicy().verticalPolicy() == QSizePolicy.Fixed

    page.close()
    window.close()
    application.quit()
