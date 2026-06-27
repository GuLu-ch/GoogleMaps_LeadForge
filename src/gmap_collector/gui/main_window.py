from datetime import datetime

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import QSize
from qfluentwidgets import FluentIcon, FluentWindow, MessageBox, NavigationItemPosition

from gmap_collector.common.paths import get_project_root, resolve_project_path
from gmap_collector.config.loader import load_app_config, load_locations_config
from gmap_collector.exporters.business_exporter import export_businesses_to_csv, export_businesses_to_excel
from gmap_collector.gui.result_page import ResultPage
from gmap_collector.gui.settings_page import SettingsPage
from gmap_collector.gui.task_config_page import TaskConfigPage
from gmap_collector.gui.task_run_page import TaskRunPage
from gmap_collector.gui.task_worker import TaskWorker
from gmap_collector.storage.database import initialize_database
from gmap_collector.storage.repositories import BusinessRepository
from gmap_collector.storage.task_repository import KeywordTaskCreate, TaskRepository
from scripts.cleanup_runtime_data import cleanup_runtime_data


class MainWindow(FluentWindow):
    """应用主窗口。

    使用 PySide6-Fluent-Widgets 的左侧导航承载四个核心页面。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoogleMaps_LeadForge")
        self.setMinimumSize(QSize(1100, 720))
        self.resize(QSize(1180, 760))
        self.navigationInterface.setExpandWidth(220)
        self._init_pages()

    def _init_pages(self) -> None:
        """初始化左侧导航页面。"""
        project_root = get_project_root()
        app_config = load_app_config(project_root / "config" / "app_config.json")
        locations_config = load_locations_config(project_root / "config" / "locations.de.json")
        database_path = resolve_project_path(app_config.paths.database)
        initialize_database(database_path)
        self.task_repository = TaskRepository(database_path)
        self.business_repository = BusinessRepository(database_path)
        self.database_path = database_path
        self.app_config = app_config
        self.current_batch_id: int | None = None
        self.task_worker: TaskWorker | None = None

        self.task_config_page = TaskConfigPage(app_config=app_config, locations_config=locations_config, parent=self)
        self.task_run_page = TaskRunPage(self)
        self.result_page = ResultPage(self)
        self.settings_page = SettingsPage(project_root=project_root, app_config=app_config, parent=self)

        self.addSubInterface(self.task_config_page, FluentIcon.EDIT, "任务配置")
        self.addSubInterface(self.task_run_page, FluentIcon.PLAY, "任务执行")
        self.addSubInterface(self.result_page, FluentIcon.VIEW, "结果管理")
        settings_item = self.addSubInterface(
            self.settings_page,
            FluentIcon.SETTING,
            "设置",
            NavigationItemPosition.BOTTOM,
        )
        settings_item.setProperty("position", NavigationItemPosition.BOTTOM)
        self._connect_page_actions()
        self.restore_latest_resumable_batch()

    def _connect_page_actions(self) -> None:
        """连接跨页面动作。"""
        self.task_config_page.create_task_button.clicked.connect(self.create_task_batch_from_preview)
        self.result_page.refresh_button.clicked.connect(self.refresh_results)
        self.task_run_page.start_button.clicked.connect(self.start_current_batch)
        self.task_run_page.resume_button.clicked.connect(self.start_current_batch)
        self.task_run_page.pause_button.clicked.connect(self.pause_current_batch)
        self.task_run_page.stop_button.clicked.connect(self.stop_current_batch)
        self.task_run_page.retry_failed_button.clicked.connect(self.retry_failed_tasks)
        self.task_run_page.export_button.clicked.connect(self.export_results_to_csv)
        self.result_page.export_csv_button.clicked.connect(self.export_results_to_csv)
        self.result_page.export_excel_button.clicked.connect(self.export_results_to_excel)
        self.settings_page.clear_runtime_data_button.clicked.connect(self.clear_runtime_data_from_settings)

    def create_task_batch_from_preview(self) -> None:
        """从任务配置页预览创建任务批次。"""
        preview_tasks = self.task_config_page.generate_preview()
        if not preview_tasks:
            self.task_run_page.append_log("没有可创建的关键词任务，请先选择地区并输入关键词。")
            return

        runtime_config = self._build_runtime_config_snapshot()
        batch_id = self.task_repository.create_batch("GUI 创建任务", runtime_config=runtime_config)
        self.task_repository.add_keyword_tasks(
            batch_id,
            [
                KeywordTaskCreate(
                    keyword=task.industry_keyword,
                    country_name=task.country_name,
                    country_search_name=task.country_search_name,
                    region_name=task.region_name,
                    region_search_name=task.region_search_name,
                    city_name=task.city_name,
                    city_search_name=task.city_search_name,
                    query_text=task.query_text,
                    search_url=task.search_url,
                )
                for task in preview_tasks
            ],
        )
        self.current_batch_id = batch_id
        self.refresh_task_run_page()
        self.switchTo(self.task_run_page)
        self.task_run_page.append_log(f"已创建任务批次：{batch_id}，关键词任务数：{len(preview_tasks)}")

    def refresh_task_run_page(self) -> None:
        """刷新任务执行页。"""
        if self.current_batch_id is None:
            return
        batch = self.task_repository.get_batch(self.current_batch_id)
        tasks = self.task_repository.list_keyword_tasks(self.current_batch_id)
        self.task_run_page.load_tasks(
            batch=batch,
            tasks=tasks,
            runtime_config=self._current_runtime_config(),
            business_stats=self.business_repository.get_business_stats(),
            consecutive_failures=self._consecutive_failure_count(tasks),
        )

    def refresh_results(self) -> None:
        """刷新结果管理页。"""
        self.result_page.load_businesses(self.business_repository.list_businesses())

    def start_current_batch(self) -> None:
        """启动或继续当前任务批次。"""
        if self.current_batch_id is None:
            self.task_run_page.append_log("当前没有可执行的任务批次。")
            return
        if self.task_worker is not None and self.task_worker.isRunning():
            self.task_run_page.append_log("任务正在运行中。")
            return

        runtime_config = self._current_runtime_config()
        if str(runtime_config["engine_name"]).lower() != "selenium":
            self.task_run_page.append_log("当前版本只支持 Selenium 执行采集；Playwright 引擎保留为后续扩展。")
            return

        next_task = self.task_repository.get_next_pending_task(self.current_batch_id)
        self.task_run_page.show_starting_state(
            runtime_config=runtime_config,
            task=next_task,
            business_stats=self.business_repository.get_business_stats(),
        )

        self.task_worker = TaskWorker(
            batch_id=self.current_batch_id,
            database_path=self.database_path,
            browser_name=str(runtime_config["browser_name"]),
            page_load_timeout_seconds=int(runtime_config["page_load_timeout_seconds"]),
            page_initial_wait_seconds=float(runtime_config["page_initial_wait_seconds"]),
            max_scroll_rounds=int(runtime_config["max_scroll_rounds"]),
            no_new_results_threshold=int(runtime_config["no_new_results_threshold"]),
            scroll_wait_seconds_min=float(runtime_config["scroll_wait_seconds_min"]),
            scroll_wait_seconds_max=float(runtime_config["scroll_wait_seconds_max"]),
            keyword_wait_seconds_min=float(runtime_config["keyword_wait_seconds_min"]),
            keyword_wait_seconds_max=float(runtime_config["keyword_wait_seconds_max"]),
            failure_threshold=int(runtime_config["failure_threshold"]),
            selenium_cache_dir=resolve_project_path(self.app_config.paths.selenium_cache_dir),
            parent=self,
        )
        self.task_worker.log_message.connect(self.task_run_page.append_log)
        self.task_worker.task_changed.connect(self.refresh_task_run_page)
        self.task_worker.finished_summary.connect(self.on_task_worker_finished)
        self.task_run_page.append_log(f"开始执行任务批次：{self.current_batch_id}")
        self.task_worker.start()

    def pause_current_batch(self) -> None:
        """请求暂停当前任务批次。"""
        if self.task_worker is not None and self.task_worker.isRunning():
            self.task_worker.request_pause()
            self.task_run_page.append_log("已请求暂停，当前关键词完成后暂停。")

    def stop_current_batch(self) -> None:
        """请求停止当前任务批次。"""
        if self.task_worker is not None and self.task_worker.isRunning():
            self.task_worker.request_stop()
            self.task_run_page.append_log("已请求停止，当前关键词完成后停止。")

    def retry_failed_tasks(self) -> None:
        """将当前批次中的失败关键词还原为待执行。"""
        if self.current_batch_id is None:
            self.task_run_page.append_log("当前没有可重试的任务批次。")
            return
        reset_count = self.task_repository.reset_failed_tasks_to_pending(self.current_batch_id)
        self.task_repository.refresh_batch_counts(self.current_batch_id)
        self.refresh_task_run_page()
        self.task_run_page.append_log(f"已重置失败关键词：{reset_count} 个。")

    def on_task_worker_finished(self, summary) -> None:
        """任务线程结束后刷新页面。"""
        self.refresh_task_run_page()
        self.refresh_results()
        if summary.paused_by_failure_threshold:
            self.task_run_page.append_log("连续失败达到阈值，任务已自动暂停。")
        elif summary.paused_by_user:
            self.task_run_page.append_log("任务已暂停。")
        elif summary.stopped_by_user:
            self.task_run_page.append_log("任务已停止。")
        else:
            self.task_run_page.append_log("任务执行完成。")

    def export_results_to_csv(self) -> None:
        """导出去重商家结果为 CSV。"""
        output_path = self._export_path("csv")
        export_businesses_to_csv(self.database_path, output_path)
        self.task_run_page.append_log(f"已导出 CSV：{output_path}")
        self.result_page.detail_view.setText(f"已导出 CSV：{output_path}")

    def export_results_to_excel(self) -> None:
        """导出去重商家结果为 Excel。"""
        output_path = self._export_path("xlsx")
        export_businesses_to_excel(self.database_path, output_path)
        self.task_run_page.append_log(f"已导出 Excel：{output_path}")
        self.result_page.detail_view.setText(f"已导出 Excel：{output_path}")

    def clear_runtime_data_from_settings(self) -> None:
        """从设置页清空本地运行数据和浏览器缓存。

        这是危险操作，会删除 SQLite 数据库、日志、导出、调试输出和浏览器用户缓存。
        因此执行前必须弹出二次确认，避免误删当前采集结果或 Google 登录状态。
        """
        if self.task_worker is not None and self.task_worker.isRunning():
            self.task_run_page.append_log("任务正在运行，不能清空数据库和缓存。")
            return
        if not self._confirm_clear_runtime_data():
            self.task_run_page.append_log("已取消清空数据库和缓存。")
            return

        project_root = get_project_root()
        removed_paths = cleanup_runtime_data(
            project_root,
            include_browser_cache=True,
            reset_locked_database=True,
        )
        initialize_database(self.database_path)
        self.task_repository = TaskRepository(self.database_path)
        self.business_repository = BusinessRepository(self.database_path)
        self.current_batch_id = None
        self.task_run_page.load_tasks(
            batch={
                "status": "pending",
                "total_keywords": 0,
                "completed_keywords": 0,
                "failed_keywords": 0,
            },
            tasks=[],
            runtime_config=self._default_runtime_config(),
            business_stats=self.business_repository.get_business_stats(),
            consecutive_failures=0,
        )
        self.refresh_results()
        if removed_paths:
            removed_text = "、".join(str(path) for path in removed_paths)
            self.task_run_page.append_log(f"已清空运行数据和缓存：{removed_text}")
            self.result_page.detail_view.setText(f"已清空运行数据和缓存：{removed_text}")
        else:
            self.task_run_page.append_log("没有需要清空的运行数据或缓存。")
            self.result_page.detail_view.setText("没有需要清空的运行数据或缓存。")

    def _confirm_clear_runtime_data(self) -> bool:
        """弹出清理确认框，确认后才允许删除本地运行数据。"""
        message_box = MessageBox(
            "确认清空数据库和缓存",
            "此操作会删除 SQLite 数据库、日志、导出文件、调试输出和浏览器登录缓存。配置文件、源码和关键词文件不会被删除。是否继续？",
            self,
        )
        message_box.yesButton.setText("确认清空")
        message_box.cancelButton.setText("取消")
        return message_box.exec() == QDialog.Accepted

    def _export_path(self, extension: str):
        """生成导出文件路径。"""
        export_dir = resolve_project_path(self.app_config.paths.export_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return export_dir / f"businesses_{timestamp}.{extension}"

    def restore_latest_resumable_batch(self) -> None:
        """启动时恢复最近一个仍可继续处理的任务批次。"""
        batch_id = self.task_repository.get_latest_resumable_batch_id()
        if batch_id is None:
            return
        self.current_batch_id = batch_id
        self.refresh_task_run_page()
        self.task_run_page.append_log(f"已恢复最近任务批次：{batch_id}")

    def _build_runtime_config_snapshot(self) -> dict[str, int | float | str]:
        """读取任务配置页控件，生成本次任务运行参数快照。"""
        return {
            "browser_name": self.task_config_page.browser_combo.currentText().lower(),
            "engine_name": self.task_config_page.engine_combo.currentText().lower(),
            "page_initial_wait_seconds": self.task_config_page.page_initial_wait_spin.value(),
            "keyword_wait_seconds_min": self.task_config_page.keyword_wait_min_spin.value(),
            "keyword_wait_seconds_max": self.task_config_page.keyword_wait_max_spin.value(),
            "scroll_wait_seconds_min": self.task_config_page.scroll_wait_min_spin.value(),
            "scroll_wait_seconds_max": self.task_config_page.scroll_wait_max_spin.value(),
            "max_scroll_rounds": self.task_config_page.max_scroll_rounds_spin.value(),
            "no_new_results_threshold": self.task_config_page.no_new_results_spin.value(),
            "page_load_timeout_seconds": self.task_config_page.page_timeout_spin.value(),
            "failure_threshold": self.task_config_page.failure_threshold_spin.value(),
        }

    def _current_runtime_config(self) -> dict[str, int | float | str]:
        """读取当前批次保存的运行参数快照，并用应用默认值兜底。"""
        if self.current_batch_id is None:
            return self._default_runtime_config()
        batch = self.task_repository.get_batch(self.current_batch_id)
        runtime_config = self._default_runtime_config()
        runtime_config.update(batch.get("runtime_config", {}))
        return runtime_config

    def _default_runtime_config(self) -> dict[str, int | float | str]:
        """根据全局配置生成运行参数默认值。"""
        return {
            "browser_name": self.app_config.browser.default_browser,
            "engine_name": self.app_config.browser.default_engine,
            "page_initial_wait_seconds": self.app_config.crawler.page_initial_wait_seconds,
            "keyword_wait_seconds_min": self.app_config.crawler.keyword_wait_seconds_min,
            "keyword_wait_seconds_max": self.app_config.crawler.keyword_wait_seconds_max,
            "scroll_wait_seconds_min": self.app_config.crawler.scroll_wait_seconds_min,
            "scroll_wait_seconds_max": self.app_config.crawler.scroll_wait_seconds_max,
            "max_scroll_rounds": self.app_config.crawler.max_scroll_rounds,
            "no_new_results_threshold": self.app_config.crawler.max_no_new_results_rounds,
            "page_load_timeout_seconds": self.app_config.crawler.page_load_timeout_seconds,
            "failure_threshold": self.app_config.crawler.consecutive_failure_pause_threshold,
        }

    def _consecutive_failure_count(self, tasks: list[dict]) -> int:
        """根据当前关键词队列估算连续失败次数。"""
        count = 0
        for task in tasks:
            status = task.get("status")
            if status == "success":
                count = 0
            elif status == "failed":
                count += 1
            elif status in {"pending", "running"}:
                break
        return count
