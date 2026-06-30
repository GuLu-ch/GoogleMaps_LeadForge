# 项目结构说明

本文档记录项目目录结构和各目录职责。每次新增、删除、移动目录或关键文件时，必须同步更新本文档。

## 当前目录结构

```text
GMap/
├── README.md
├── AGENTS.md
├── CHANGELOG.md
├── pyproject.toml
├── pytest.ini
├── requirements.txt
├── environment.yml
├── GoogleMaps_LeadForge.spec
├── .gitignore
├── config/
│   ├── app_config.json
│   └── locations.json
├── data/
│   └── app.sqlite3
├── drivers/
│   ├── selenium-cache/
│   └── playwright-browsers/
├── exports/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── scripts/
│   ├── __init__.py
│   ├── build_windows_release.ps1
│   ├── cleanup_runtime_data.py
│   ├── generate_locations_config.py
│   └── open_login_browser.py
├── docs/
│   ├── REQUIREMENTS.md
│   ├── DESIGN.md
│   ├── PROJECT_STRUCTURE.md
│   ├── DEVELOPMENT_WORKFLOW.md
│   └── superpowers/
│       ├── plans/
│       │   └── 2026-06-27-gmap-collector-mvp.md
│       └── specs/
│           └── 2026-06-27-gmap-collector-design.md
├── src/
│   └── gmap_collector/
│       ├── __init__.py
│       ├── main.py
│       ├── app.py
│       ├── common/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   └── paths.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   └── schemas.py
│       ├── gui/
│       │   ├── __init__.py
│       │   ├── fluent_components.py
│       │   ├── layout_utils.py
│       │   ├── main_window.py
│       │   ├── result_page.py
│       │   ├── settings_page.py
│       │   ├── table_utils.py
│       │   ├── task_config_page.py
│       │   ├── task_run_page.py
│       │   ├── task_worker.py
│       │   ├── website_exploration_page.py
│       │   └── website_exploration_worker.py
│       ├── tasks/
│       │   ├── __init__.py
│       │   └── keyword_builder.py
│       ├── browser/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── playwright_engine.py
│       │   └── selenium_engine.py
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── maps_list_parser.py
│       │   └── website_info_parser.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── maps_crawler.py
│       │   ├── task_runner.py
│       │   ├── website_crawler.py
│       │   └── website_exploration_service.py
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   ├── repositories.py
│       │   ├── task_repository.py
│       │   └── website_exploration_repository.py
│       └── exporters/
│           ├── __init__.py
│           └── business_exporter.py
└── tests/
    └── unit/
        ├── test_config_loader.py
        ├── test_database.py
        ├── test_exporter.py
        ├── test_generate_locations_config.py
        ├── test_gui_layout.py
        ├── test_keyword_builder.py
        ├── test_maps_crawler_service.py
        ├── test_maps_list_parser.py
        ├── test_cleanup_runtime_data.py
        ├── test_open_login_browser.py
        ├── test_repositories.py
        ├── test_selenium_engine.py
        ├── test_task_repository.py
        ├── test_task_runner.py
        ├── test_website_crawler.py
        ├── test_website_exploration_repository.py
        ├── test_website_exploration_service.py
        ├── test_website_exploration_worker.py
        └── test_website_info_parser.py
```

## 根目录文件

### README.md

项目主说明文档，面向用户和开发者。

### AGENTS.md

面向 Codex、AI 智能体和人工开发者的开发规范。

### CHANGELOG.md

中文更新记录。

### pyproject.toml

Python 包元数据文件。

负责：

- 定义项目包名 `gmap-collector`。
- 声明 Python 版本范围。
- 指定 `src/` 布局。
- 支持可编辑安装，便于使用 `python -m gmap_collector.main` 启动。

### pytest.ini

pytest 测试配置。

负责：

- 指定测试目录。
- 指定 `src` 为测试导入路径。

### requirements.txt

pip 依赖列表，明确标注核心依赖版本。

### environment.yml

Anaconda 环境配置，环境名称固定为 `gmap`。

### GoogleMaps_LeadForge.spec

PyInstaller 打包配置。

负责：

- 使用 `src/gmap_collector/main.py` 作为 Windows exe 入口。
- 收集 `qfluentwidgets` 所需数据文件和隐藏导入。
- 生成 `GoogleMaps_LeadForge` onedir 可分发目录。

### .gitignore

忽略本地环境、缓存、数据库、日志、导出文件、浏览器缓存、本地关键词文件、调试输出、临时诊断脚本和本地测试数据样本。

## config/

配置文件目录。所有可迁移、可手动修改的配置都放在这里。

- `app_config.json`：运行配置，包括浏览器、引擎、停留时间、滚动策略、失败阈值、路径配置。
- `locations.json`：全国家地区配置，包括国家、地区/州、城市、中文显示名和搜索用名称。

## data/

本地数据目录。正式运行后由程序创建 `app.sqlite3`。

SQLite 负责保存：

- 任务批次。
- 关键词任务。
- 商家记录。
- 商家命中关系。
- 任务运行参数快照。

## drivers/

浏览器用户数据和自动化工具缓存目录。

- `selenium-cache/`：Chrome/Edge 的项目内用户数据目录，用于保存登录态、Cookie、Profile 等浏览器状态；登录脚本和正式采集任务会复用该目录。
- `playwright-browsers/`：Playwright 浏览器缓存目录。

## exports/

导出目录，保存 CSV 和 Excel 文件。

## logs/

日志目录，保存运行日志、错误日志和调试日志。

## scripts/

项目辅助脚本目录。

- `cleanup_runtime_data.py`：清理本地运行数据库、日志、导出、调试输出和截图；默认保留关键词输入、配置文件和浏览器登录缓存，传入参数或由 GUI 设置页调用时可同步清理浏览器缓存；数据库文件被占用时可清空 Google Maps 任务、商家、命中关系和官网探索相关业务表作为兜底。
- `build_windows_release.ps1`：调用 PyInstaller 构建 Windows onedir 发行版，并把 `config/`、运行目录、README、LICENSE 和 CHANGELOG 复制到 exe 同级目录后生成 zip 包。
- `generate_locations_config.py`：一次性地区配置生成脚本，负责从本地国家 HTML 表和城市 JSON 数据生成 `config/locations.json`。
- `open_login_browser.py`：直接启动系统真实 Chrome/Edge 进程打开 Google 登录页，并使用采集任务相同的项目内浏览器用户目录，便于后续采集复用登录状态；Chrome 默认优先使用 `chrome_proxy.exe`。

## docs/

项目文档目录。

- `REQUIREMENTS.md`：需求说明。
- `DESIGN.md`：技术设计。
- `PROJECT_STRUCTURE.md`：项目结构说明。
- `DEVELOPMENT_WORKFLOW.md`：开发流程。
- `superpowers/specs/`：设计规格快照。
- `superpowers/plans/`：实现计划。

## src/gmap_collector/

源码主目录。

### main.py

程序入口文件。

负责：

- 解析命令行参数。
- 支持 `--check` 初始化验证。
- 启动 GUI。

### app.py

应用装配文件。

当前已实现：

- 创建 `QApplication`。
- 创建主窗口。

### common/

公共模块。

当前已实现：

- `models.py`：商家记录等通用数据结构。
- `paths.py`：项目根目录和项目内路径解析。

### config/

配置模块。

当前已实现：

- `schemas.py`：配置数据结构。
- `loader.py`：读取运行配置和地区配置。

### gui/

GUI 模块。

当前已实现：

- `main_window.py`：PySide6-Fluent-Widgets 左侧导航主窗口，负责跨页面动作、任务运行、导出以及设置页清理运行数据和缓存的维护操作。
- `fluent_components.py`：Fluent UI 通用组件，包含防滚轮误触数字输入框、指标卡片、通用分区卡片、按钮行、路径卡片和文本信息行。
- `layout_utils.py`：页面级自适应布局工具，统一创建滚动内容区和固定操作栏。
- `task_config_page.py`：任务配置页控件，负责国家地区选择、地区复选框局部滚动区域、关键词、本次任务运行参数和任务预览表。
- `task_run_page.py`：任务执行页控件，负责任务控制按钮、状态面板、关键词队列和运行日志。
- `task_worker.py`：GUI 后台任务线程，负责在不阻塞主界面的情况下驱动 Selenium 执行当前批次。
- `website_exploration_page.py`：官网探索页控件，负责来源任务选择、官网探索参数、探索批次选择、探索状态统计和探索任务列表展示。
- `website_exploration_worker.py`：官网探索后台线程，负责顺序执行官网探索任务，并在静态请求失败或无核心联系方式时按需启动 Selenium 浏览器兜底。
- `result_page.py`：结果管理页控件，负责筛选条件、商家结果表和详情区。
- `settings_page.py`：设置页控件，负责外观主题、全局默认运行参数、项目路径和清空数据库/缓存按钮；项目开发文档不在该页面展示。
- `table_utils.py`：表格列宽策略工具，统一处理默认列宽、手动拖拽、长列拉伸和滚动条策略。

### tasks/

任务模块。

当前已实现：

- `keyword_builder.py`：搜索词、Google Maps URL 和任务输入生成。

后续将扩展：

- 街道级任务组合。
- CSV/JSON 导入地区配置。
- 更复杂的任务批次管理。

### browser/

浏览器引擎模块。

当前已实现：

- `base.py`：浏览器引擎统一接口。
- `selenium_engine.py`：Selenium 引擎，支持可视化 Chrome/Edge、运行时 DOM 快照、语言无关结果等待和列表滚动。
- `playwright_engine.py`：Playwright 引擎骨架。

说明：Selenium 是第一版优先落地引擎；Playwright 保留为后续可插拔扩展。

### parsers/

页面解析模块。

当前已实现：

- `maps_list_parser.py`：解析 Google Maps 列表页商家卡片，提取名称、地址、电话、官网、评分、评论数量、分类和 Google Maps 链接；缺失字段保留空字符串。
- `website_info_parser.py`：解析商家官网 HTML，提取电话、邮箱、Instagram、TikTok、Twitter / X、Facebook、LinkedIn、YouTube、WhatsApp 和 SEO Keywords。

### services/

服务模块。

当前已实现：

- `maps_crawler.py`：单个 Google Maps 搜索链接的采集服务，负责打开链接、等待结果 DOM、页面初始停留、滚动随机停留、解析结果、写入 SQLite 和记录命中关系。
- `task_runner.py`：任务运行器，负责单线程顺序执行关键词任务、关键词间随机停留、暂停、停止和连续失败自动暂停。
- `website_crawler.py`：官网静态抓取服务，负责按探索深度和最大页面数遍历同主域及其子域页面，并合并多页官网信息。
- `website_exploration_service.py`：官网探索单任务执行服务，负责领取待执行官网任务、调用静态抓取、判断核心联系方式、执行浏览器兜底、写回结果或失败原因。

### storage/

存储模块。

当前已实现：

- `database.py`：SQLite 表结构初始化，并兼容旧数据库自动追加新增字段。
- `repositories.py`：商家记录 upsert、Google Maps 链接去重、来源关键词合并。
- `task_repository.py`：任务批次和关键词任务仓储，支持运行参数快照、状态流转、失败重试和最近可恢复批次查询。
- `website_exploration_repository.py`：官网探索任务仓储，负责从 Google Maps 批次创建二次任务、维护探索批次状态和探索任务状态。

### exporters/

导出模块。

当前已实现：

- `business_exporter.py`：从 SQLite 去重结果导出 CSV 和 Excel。
  支持按 Task 批次过滤导出，导出字段和结果管理页保持一致。

## tests/

测试目录。

当前单元测试覆盖：

- 配置读取。
- 关键词生成。
- URL 生成。
- SQLite 初始化。
- SQLite 去重。
- 来源关键词合并。
- CSV 导出。
- Excel 导出。
- 全国家地区配置生成脚本。
- GUI 设置页基础控件、外观设置分组、维护按钮和项目文档入口移除规则。
- GUI Fluent 表格列宽策略、平滑滚动和手动拖拽调整。
- GUI 任务执行页状态反馈、不确定进度条和启动中展示。
- GUI 页面自适应布局、主窗口默认尺寸、侧边导航展开宽度和防滚轮误触数字输入框。
- GUI 任务配置页地区复选框局部滚动区域，以及少量地区时的固定行高。
- Google Maps 列表页解析。
- Selenium 等待条件语言无关约束。
- Google Maps 单链接采集服务。
- 任务批次仓储、运行参数快照、失败重试和最近可恢复批次查询。
- 任务运行器的顺序执行、关键词间停留、暂停和连续失败暂停。
- 本地运行产物清理脚本，包括可选清理浏览器缓存。
- 设置页清空数据库和缓存按钮，以及清理后重新初始化数据库的主窗口流程。
- 官网信息解析器，覆盖电话、邮箱、社媒链接和 SEO Keywords 提取。
- 官网静态抓取服务，覆盖深度限制、同主域限制、请求失败继续处理和超时参数传递。
- 官网探索服务，覆盖结果写回、失败标记、浏览器兜底和最终状态统计。
- 官网探索后台线程浏览器兜底逻辑。
- GUI 任务化选择、运行中锁定、官网探索按来源任务过滤批次和探索状态卡片。
- 登录浏览器脚本真实浏览器启动方式和项目内用户数据目录。
