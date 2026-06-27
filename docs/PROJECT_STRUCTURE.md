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
├── .gitignore
├── config/
│   ├── app_config.json
│   └── locations.de.json
├── data/
│   └── app.sqlite3
├── drivers/
│   ├── selenium-cache/
│   └── playwright-browsers/
├── exports/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
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
│       │   ├── main_window.py
│       │   ├── result_page.py
│       │   ├── settings_page.py
│       │   ├── table_utils.py
│       │   ├── task_config_page.py
│       │   └── task_run_page.py
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
│       │   └── maps_list_parser.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── maps_crawler.py
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   └── repositories.py
│       └── exporters/
│           ├── __init__.py
│           └── business_exporter.py
└── tests/
    └── unit/
        ├── test_config_loader.py
        ├── test_database.py
        ├── test_exporter.py
        ├── test_gui_layout.py
        ├── test_keyword_builder.py
        └── test_repositories.py
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

### .gitignore

忽略本地环境、缓存、数据库、日志、导出文件、浏览器缓存、本地关键词文件、调试输出和临时诊断脚本。

## config/

配置文件目录。所有可迁移、可手动修改的配置都放在这里。

- `app_config.json`：运行配置，包括浏览器、引擎、停留时间、滚动策略、失败阈值、路径配置。
- `locations.de.json`：德国地区配置，包括国家、地区/州、城市、中文显示名和搜索用名称。

## data/

本地数据目录。正式运行后由程序创建 `app.sqlite3`。

SQLite 负责保存：

- 任务批次。
- 关键词任务。
- 商家记录。
- 商家命中关系。

## drivers/

浏览器驱动和自动化工具缓存目录。

- `selenium-cache/`：Selenium Manager 或浏览器驱动相关缓存目录。
- `playwright-browsers/`：Playwright 浏览器缓存目录。

## exports/

导出目录，保存 CSV 和 Excel 文件。

## logs/

日志目录，保存运行日志、错误日志和调试日志。

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

- `main_window.py`：PySide6-Fluent-Widgets 左侧导航主窗口。
- `layout_utils.py`：页面级自适应布局工具，统一创建滚动内容区和固定操作栏。
- `task_config_page.py`：任务配置页控件，负责地区、关键词、本次任务运行参数和任务预览表。
- `task_run_page.py`：任务执行页控件，负责任务控制按钮、状态面板、关键词队列和运行日志。
- `result_page.py`：结果管理页控件，负责筛选条件、商家结果表和详情区。
- `settings_page.py`：设置与文档页控件，负责展示全局默认运行参数、项目路径和文档入口。
- `table_utils.py`：表格列宽策略工具，统一处理默认列宽、手动拖拽、长列拉伸和滚动条策略。

### tasks/

任务模块。

当前已实现：

- `keyword_builder.py`：搜索词、Google Maps URL 和任务输入生成。

后续将扩展：

- 批次创建。
- 关键词队列。
- 暂停继续。
- 失败重试。
- 连续失败暂停。

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

### services/

服务模块。

当前已实现：

- `maps_crawler.py`：单个 Google Maps 搜索链接的采集服务，负责打开链接、滚动列表、解析结果并写入 SQLite。

### storage/

存储模块。

当前已实现：

- `database.py`：SQLite 表结构初始化。
- `repositories.py`：商家记录 upsert、Google Maps 链接去重、来源关键词合并。

### exporters/

导出模块。

当前已实现：

- `business_exporter.py`：从 SQLite 去重结果导出 CSV 和 Excel。

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
- GUI 设置页基础控件。
- GUI 表格列宽策略。
- Google Maps 列表页解析。
- Selenium 等待条件语言无关约束。
- Google Maps 单链接采集服务。
