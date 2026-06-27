# Google Maps 商家信息采集工具第一版实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建第一版可运行的桌面软件骨架，包含配置读取、任务生成、SQLite 持久化、导出、PySide6-Fluent-Widgets 左侧导航 GUI，以及可插拔浏览器引擎接口。

**Architecture:** 项目采用分层架构：GUI 层负责界面，任务层负责队列和状态，浏览器层负责 Selenium/Playwright 接口，解析层负责 DOM 数据提取，存储层负责 SQLite，导出层负责 CSV/Excel。第一阶段先实现可测试的本地功能和 GUI 壳，Google Maps 实际 DOM 定位在用户协助确认后再完善。

**Tech Stack:** Python 3.11、Anaconda、PySide6、PySide6-Fluent-Widgets、SQLite、Selenium、Playwright、pandas、openpyxl、pytest。

---

## 文件结构

第一版开发将创建以下源码和测试文件：

```text
src/gmap_collector/
├── __init__.py
├── main.py
├── app.py
├── common/
│   ├── __init__.py
│   ├── paths.py
│   └── models.py
├── config/
│   ├── __init__.py
│   ├── loader.py
│   └── schemas.py
├── storage/
│   ├── __init__.py
│   ├── database.py
│   └── repositories.py
├── tasks/
│   ├── __init__.py
│   ├── keyword_builder.py
│   └── task_service.py
├── exporters/
│   ├── __init__.py
│   └── business_exporter.py
├── browser/
│   ├── __init__.py
│   ├── base.py
│   ├── selenium_engine.py
│   └── playwright_engine.py
├── parsers/
│   ├── __init__.py
│   └── maps_list_parser.py
└── gui/
    ├── __init__.py
    ├── main_window.py
    ├── task_config_page.py
    ├── task_run_page.py
    ├── result_page.py
    └── settings_page.py
```

测试文件：

```text
tests/unit/
├── test_config_loader.py
├── test_keyword_builder.py
├── test_database.py
├── test_repositories.py
└── test_exporter.py
```

## Task 1: 环境和依赖验证

**Files:**
- Modify: `requirements.txt`
- Modify: `environment.yml`
- Modify: `docs/PROJECT_STRUCTURE.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: 创建 Conda 环境**

Run:

```powershell
conda create -n gmap python=3.11 -y
```

Expected: 创建名为 `gmap` 的环境。

- [ ] **Step 2: 安装依赖**

Run:

```powershell
conda run -n gmap python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

Expected: 所有依赖安装完成。

- [ ] **Step 3: 验证关键包导入**

Run:

```powershell
conda run -n gmap python -c "import PySide6; import qfluentwidgets; import selenium; import playwright; import pandas; import openpyxl; print('OK')"
```

Expected: 输出 `OK`。

- [ ] **Step 4: 更新文档**

确认 `README.md`、`docs/DEVELOPMENT_WORKFLOW.md`、`docs/PROJECT_STRUCTURE.md` 已记录环境名称、依赖文件和驱动目录。

## Task 2: 配置读取模块

**Files:**
- Create: `src/gmap_collector/__init__.py`
- Create: `src/gmap_collector/common/paths.py`
- Create: `src/gmap_collector/config/schemas.py`
- Create: `src/gmap_collector/config/loader.py`
- Test: `tests/unit/test_config_loader.py`

- [ ] **Step 1: 写配置读取失败测试**

测试目标：读取现有 JSON 配置，能得到国家、地区、城市和运行参数。

- [ ] **Step 2: 运行测试确认失败**

Run:

```powershell
conda run -n gmap pytest tests/unit/test_config_loader.py -v
```

Expected: 因模块不存在失败。

- [ ] **Step 3: 实现最小配置读取**

实现 `load_app_config()` 和 `load_locations_config()`。

- [ ] **Step 4: 运行测试确认通过**

Run:

```powershell
conda run -n gmap pytest tests/unit/test_config_loader.py -v
```

Expected: PASS。

## Task 3: 关键词和 URL 生成

**Files:**
- Create: `src/gmap_collector/tasks/keyword_builder.py`
- Test: `tests/unit/test_keyword_builder.py`

- [ ] **Step 1: 写关键词组合测试**

测试目标：行业关键词、城市、地区、国家能组合成 `Car Wrap Shop in Biberach, Baden-Wuerttemberg, Germany`。

- [ ] **Step 2: 写 URL 编码测试**

测试目标：搜索词能生成 Google Maps URL。

- [ ] **Step 3: 运行测试确认失败**

Run:

```powershell
conda run -n gmap pytest tests/unit/test_keyword_builder.py -v
```

Expected: 因模块不存在失败。

- [ ] **Step 4: 实现关键词生成**

实现 `build_query_text()` 和 `build_google_maps_search_url()`。

- [ ] **Step 5: 运行测试确认通过**

Run:

```powershell
conda run -n gmap pytest tests/unit/test_keyword_builder.py -v
```

Expected: PASS。

## Task 4: SQLite 初始化和去重

**Files:**
- Create: `src/gmap_collector/storage/database.py`
- Create: `src/gmap_collector/storage/repositories.py`
- Create: `src/gmap_collector/common/models.py`
- Test: `tests/unit/test_database.py`
- Test: `tests/unit/test_repositories.py`

- [ ] **Step 1: 写数据库初始化测试**

测试目标：初始化后存在 `task_batches`、`keyword_tasks`、`businesses`、`business_task_hits` 表。

- [ ] **Step 2: 写商家去重测试**

测试目标：相同 Google Maps 链接只保存一条商家记录，来源关键词用英文逗号合并。

- [ ] **Step 3: 运行测试确认失败**

Run:

```powershell
conda run -n gmap pytest tests/unit/test_database.py tests/unit/test_repositories.py -v
```

Expected: 因模块不存在失败。

- [ ] **Step 4: 实现数据库和仓储**

实现 SQLite 初始化、任务写入、商家 upsert、来源关键词合并。

- [ ] **Step 5: 运行测试确认通过**

Run:

```powershell
conda run -n gmap pytest tests/unit/test_database.py tests/unit/test_repositories.py -v
```

Expected: PASS。

## Task 5: 导出模块

**Files:**
- Create: `src/gmap_collector/exporters/business_exporter.py`
- Test: `tests/unit/test_exporter.py`

- [ ] **Step 1: 写 CSV 导出测试**

测试目标：从 SQLite 查询的去重商家记录能导出 CSV。

- [ ] **Step 2: 写 Excel 导出测试**

测试目标：从 SQLite 查询的去重商家记录能导出 Excel。

- [ ] **Step 3: 运行测试确认失败**

Run:

```powershell
conda run -n gmap pytest tests/unit/test_exporter.py -v
```

Expected: 因模块不存在失败。

- [ ] **Step 4: 实现导出模块**

实现 `export_businesses_to_csv()` 和 `export_businesses_to_excel()`。

- [ ] **Step 5: 运行测试确认通过**

Run:

```powershell
conda run -n gmap pytest tests/unit/test_exporter.py -v
```

Expected: PASS。

## Task 6: 浏览器引擎接口骨架

**Files:**
- Create: `src/gmap_collector/browser/base.py`
- Create: `src/gmap_collector/browser/selenium_engine.py`
- Create: `src/gmap_collector/browser/playwright_engine.py`
- Create: `src/gmap_collector/parsers/maps_list_parser.py`

- [ ] **Step 1: 定义统一接口**

定义浏览器引擎抽象类，包含启动、关闭、打开 URL、滚动、读取 DOM、检测底部等方法。

- [ ] **Step 2: 实现 Selenium 和 Playwright 占位骨架**

只实现启动和关闭的结构，不写死 Google Maps DOM 选择器。

- [ ] **Step 3: 实现解析器空结果安全返回**

解析器在没有 DOM 输入时返回空列表。

- [ ] **Step 4: 文档同步**

如果接口和 `docs/DESIGN.md` 不一致，更新设计文档。

## Task 7: GUI 主窗口和页面骨架

**Files:**
- Create: `src/gmap_collector/main.py`
- Create: `src/gmap_collector/app.py`
- Create: `src/gmap_collector/gui/main_window.py`
- Create: `src/gmap_collector/gui/task_config_page.py`
- Create: `src/gmap_collector/gui/task_run_page.py`
- Create: `src/gmap_collector/gui/result_page.py`
- Create: `src/gmap_collector/gui/settings_page.py`

- [ ] **Step 1: 创建 PySide6-Fluent-Widgets 主窗口**

使用左侧侧边导航，创建四个页面入口。

- [ ] **Step 2: 创建任务配置页静态控件**

包含地区选择、关键词输入、运行参数、任务预览表格。

- [ ] **Step 3: 创建任务执行页静态控件**

包含开始、暂停、继续、停止、重试失败关键词、导出结果按钮，以及状态面板、关键词队列表格、日志区。

- [ ] **Step 4: 创建结果管理页静态控件**

包含筛选区、结果表格、详情区。

- [ ] **Step 5: 创建设置页静态控件**

展示外观、配置、数据库、导出、日志和维护操作，不在软件设置页展示项目开发文档入口。

- [ ] **Step 6: 启动验证**

Run:

```powershell
conda run -n gmap python -m gmap_collector.main
```

Expected: GUI 窗口可以启动。

## Task 8: 文档同步和最终验证

**Files:**
- Modify: `README.md`
- Modify: `docs/PROJECT_STRUCTURE.md`
- Modify: `docs/DESIGN.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: 运行单元测试**

Run:

```powershell
conda run -n gmap pytest tests/unit -v
```

Expected: PASS。

- [ ] **Step 2: 检查文档和代码结构**

确认 `docs/PROJECT_STRUCTURE.md` 和实际目录一致。

- [ ] **Step 3: 更新 CHANGELOG**

记录第一版骨架开发内容。

- [ ] **Step 4: 汇报验证结果**

说明已经完成的内容、未完成的 Google Maps DOM 调试项、需要用户协助确认的元素定位项。

## 自检结果

- 需求覆盖：已覆盖配置、关键词生成、SQLite、去重、导出、GUI 壳、浏览器引擎接口。
- 暂不覆盖：Google Maps 具体 DOM 选择器和真实采集字段定位，该部分需要打开页面后与用户协作确认。
- 占位扫描：计划中没有把未确认 DOM 选择器写死，避免擅自决策。
- 类型一致性：模块名称和目录结构与 `docs/PROJECT_STRUCTURE.md` 保持一致。
