# Google Maps 商家信息采集工具第一版设计规格

本文档是当前需求梳理后的设计规格快照。正式实现前，应以 `README.md`、`docs/REQUIREMENTS.md`、`docs/DESIGN.md`、`docs/PROJECT_STRUCTURE.md` 和 `AGENTS.md` 为主要依据。

## 目标

构建一个 Python 桌面软件，通过配置化地区和关键词生成 Google Maps 搜索任务，使用可视化浏览器顺序采集搜索结果列表页中的商家基础信息，并通过 SQLite 持久化、去重、恢复和导出。

## 技术路线

- Python
- Anaconda
- PySide6
- PySide6-Fluent-Widgets
- SQLite
- Selenium
- Playwright
- JSON 配置
- CSV 和 Excel 导出

## 已确认范围

- 从地区配置读取国家、地区、城市。
- GUI 中多选国家和地区。
- 地区被选中后默认包含该地区下全部城市。
- 关键词由用户在 GUI 中输入，一行一个。
- 搜索词格式为 `行业关键词 + in + 城市, 地区, 国家`。
- 默认 Chrome，同时支持 Edge。
- 默认可视化浏览器窗口。
- 单进程、单浏览器窗口。
- 支持 Selenium 和 Playwright 可插拔引擎。
- 只解析 Google Maps 搜索结果列表页。
- 不点击商家详情页。
- SQLite 持久化任务和商家记录。
- 按 Google Maps 链接全局去重。
- 来源关键词用英文逗号合并。
- 支持暂停、继续、停止、失败重试。
- 支持关闭软件后恢复任务。
- 支持连续失败达到阈值后暂停整批任务。
- 支持 CSV 和 Excel 导出。

## 已确认不做

- 街道级搜索。
- 多浏览器并发。
- 无头模式。
- 自动绕过验证码或风控。
- 登录账号管理。
- 点击商家详情页补全字段。
- 云端同步。
- 人工备注编辑。

## GUI 页面

第一版使用左侧侧边导航，包含：

- 任务配置。
- 任务执行。
- 结果管理。
- 设置与文档。

## 文档要求

项目按开源软件方式维护，必须包含：

- `README.md`
- `AGENTS.md`
- `CHANGELOG.md`
- `docs/REQUIREMENTS.md`
- `docs/DESIGN.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/DEVELOPMENT_WORKFLOW.md`

每次开发都必须同步更新相关文档。
