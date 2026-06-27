# GoogleMaps_LeadForge

一个基于 Python 的桌面工具，用于通过 Google Maps 关键词搜索批量发现、采集和管理商家线索数据。支持地区与行业关键词组合、结果去重、任务恢复，以及 CSV/Excel 导出。

> 本项目不是 Google 官方产品，也未获得 Google 赞助、认可或背书。

## 项目目标

第一版目标是构建一个稳定、可恢复、可扩展的桌面采集工具：

- 通过配置文件加载国家、地区和城市数据。
- 在图形界面中选择国家和地区，地区被选择后默认包含该地区下全部城市。
- 在界面中输入行业关键词，一行一个。
- 自动组合生成 Google Maps 搜索链接。
- 使用单进程、单浏览器窗口顺序执行采集任务。
- 支持 Chrome 和 Edge，默认使用 Chrome。
- 支持 Selenium 和 Playwright 两种浏览器自动化引擎，默认优先使用 Selenium，后续可按实际效果调整。
- 只解析 Google Maps 搜索结果列表页中已经加载出来的可见 DOM，不进入商家详情页。
- 使用 SQLite 保存任务、关键词状态和商家记录。
- 按 Google Maps 链接进行全局去重。
- 支持暂停、继续、失败重试和连续失败自动暂停。
- 从去重后的 SQLite 数据导出 CSV 和 Excel。

## 开源协议

本项目使用 `GPL-3.0-only` 协议开源。详情见 `LICENSE`。

## 第一版采集字段

第一版采集以下字段：

| 字段 | 说明 |
| --- | --- |
| 商家名称 | Google Maps 搜索结果中显示的商家名称 |
| 地址 | 列表页 DOM 中可直接解析到的地址，解析不到时允许为空 |
| 电话 | 列表页 DOM 中可直接解析到的电话，解析不到时允许为空 |
| 官网 | 列表页 DOM 中可直接解析到的官网，解析不到时允许为空 |
| 评分 | 商家评分 |
| 评论数量 | 商家评论数量 |
| 商家分类 | Google Maps 显示的行业分类，例如洗车店、汽车美容等 |
| Google Maps 链接 | 用于全局去重的主键字段 |
| 来源关键词 | 同一商家被多个行业关键词命中时，用英文逗号合并 |

## 第一版不包含的功能

以下能力不纳入第一版开发范围：

- 街道级搜索。
- 多浏览器并发。
- 无头浏览器模式。
- 自动绕过验证码、登录限制或风控页面。
- 登录账号管理。
- 点击进入商家详情页采集更完整字段。
- 云端同步。
- 人工备注编辑。

这些功能可以作为后续版本扩展，但必须先更新需求文档和设计文档，再进入开发。

## 基本工作流

1. 启动软件。
2. 软件读取 `config/locations.de.json` 和 `config/app_config.json`。
3. 在“任务配置”页选择国家和地区。
4. 在关键词输入框中输入行业关键词，一行一个。
5. 生成任务预览。
6. 创建任务并进入“任务执行”页。
7. 点击开始，软件打开可视化浏览器窗口并顺序访问 Google Maps 搜索链接。
8. 每个关键词页面持续滚动加载列表结果。
9. 达到列表底部，或连续多次滚动没有新增商家时，该关键词标记为完成。
10. 解析到的商家记录写入 SQLite，并按 Google Maps 链接去重。
11. 任务可手动暂停、继续、停止。
12. 任务完成后在“结果管理”页导出 CSV 或 Excel。

## 页面设计

第一版使用左侧侧边导航组织页面：

- 任务配置
- 任务执行
- 结果管理
- 设置与文档

左侧导航使用 `PySide6-Fluent-Widgets` 的导航组件实现。主窗口左侧固定显示页面入口，右侧显示当前页面内容。这样比顶部 Tab 更适合后续增加模块，也更符合工具型桌面软件的长期扩展需求。

页面自适应规则：

- 主窗口设置最小尺寸，避免窗口被缩到控件无法排版的状态。
- 每个功能页面使用页面级滚动区域，窗口变矮时优先滚动内容，而不是裁剪底部按钮。
- 关键操作按钮放在固定操作栏中，例如“创建任务并进入执行页”和“保存全局设置”。
- 表格、文本框和日志区设置最小高度和可扩展策略，缩放窗口时优先压缩空白区域，不让文字只显示一半。
- 任务执行页的状态区和关键词队列使用可拖动分隔器，便于不同屏幕下调整空间比例。

### 任务配置页

左侧是地区选择区：

- 国家列表。
- 地区/州复选框。
- `全选地区` 按钮。
- `取消全选` 按钮。
- `刷新配置` 按钮。

中间是行业关键词区：

- 多行文本框，一行一个关键词。
- 预计生成任务数。
- `生成任务预览` 按钮。
- `清空关键词` 按钮。

右侧是运行参数区：

- 浏览器选择：Chrome / Edge。
- 引擎选择：Selenium / Playwright。
- 页面初始停留时间。
- 每个关键词完成后的随机停留范围。
- 滚动加载间隔随机范围。
- 连续无新增停止次数。
- 最大滚动次数。
- 页面加载超时时间。
- 连续失败自动暂停阈值。
- `保存配置` 按钮。
- `恢复默认配置` 按钮。

运行参数关系：

- 设置页中的全局运行设置是新任务的默认值模板。
- 任务配置页中的运行参数是本次任务快照，初始值来自全局默认值。
- 如果在任务配置页修改运行参数，只影响本次创建的任务，不会自动回写全局默认值。
- 创建任务后，任务执行、暂停、继续和后续恢复都应使用该任务快照，避免全局设置变更影响已创建任务。

底部是任务预览表格：

- 序号。
- 行业关键词。
- 城市。
- 地区。
- 国家。
- 生成的 Google Maps 链接。
- `创建任务并进入执行页` 按钮。

### 任务执行页

顶部是任务控制栏：

- `开始`
- `暂停`
- `继续`
- `停止`
- `重试失败关键词`
- `导出结果`

中部左侧是任务状态面板：

- 总关键词数。
- 已完成数量。
- 失败数量。
- 待执行数量。
- 已采集商家数。
- 去重后商家数。
- 连续失败次数。
- 当前关键词。
- 当前城市。
- 当前浏览器引擎。

中部右侧是关键词队列表格：

- 状态。
- 行业关键词。
- 城市。
- 地区。
- 国家。
- 失败原因。
- 最后执行时间。

底部是运行日志区：

- 启动浏览器日志。
- 打开链接日志。
- 滚动加载日志。
- 本轮解析数量。
- 失败原因。
- 暂停原因。

### 结果管理页

顶部是筛选区：

- 按关键词筛选。
- 按国家筛选。
- 按地区筛选。
- 按城市筛选。
- 按商家分类筛选。
- `刷新数据` 按钮。
- `导出 CSV` 按钮。
- `导出 Excel` 按钮。

中部是商家结果表格：

- 商家名称。
- 地址。
- 电话。
- 官网。
- 评分。
- 评论数量。
- 商家分类。
- Google Maps 链接。
- 来源关键词。
- 首次采集时间。
- 最后更新时间。

底部是详情区：

- 完整 Google Maps 链接。
- 来源关键词列表。
- 采集任务信息。

### 设置与文档页

该页面用于集中管理基础全局设置、关键路径和文档入口。

全局运行设置包括：

- 默认浏览器。
- 默认自动化引擎。
- 页面初始停留秒数。
- 关键词停留随机范围。
- 滚动停留随机范围。
- 最大滚动次数。
- 连续无新增停止次数。
- 页面加载超时时间。
- 连续失败暂停阈值。

项目路径包括：

- `config/app_config.json`
- `config/locations.de.json`
- SQLite 数据库路径。
- 导出目录。
- 日志目录。
- Selenium 缓存目录。
- Playwright 浏览器目录。

文档入口包括：

- `README.md`
- `AGENTS.md`
- `docs/REQUIREMENTS.md`
- `docs/DESIGN.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/DEVELOPMENT_WORKFLOW.md`

主要表格使用“默认列宽 + 手动拖拽 + 长列拉伸”的混合策略：

- 国家、地区、城市、关键词等常用列提供更宽的默认宽度。
- 表头允许用户手动拖拽调整列宽，便于临时查看长文本。
- Google Maps 链接、失败原因等长文本列使用拉伸列承接剩余空间。
- 水平和垂直滚动条按需显示，后续数据量增大时仍然可以滚动查看。

## 技术路线

第一版采用重型可扩展方案：

- Python：主开发语言。
- Anaconda：本地开发环境管理，虚拟环境名称固定为 `gmap`。
- PySide6：桌面图形界面基础框架。
- PySide6-Fluent-Widgets：基于 PySide6 的 Fluent 风格组件库，用于构建更完整、更美观的前端界面。
- SQLite：本地持久化数据库。
- Selenium：第一浏览器自动化引擎。
- Playwright：第二浏览器自动化引擎，作为可插拔引擎保留。
- pandas / openpyxl：CSV 和 Excel 导出。
- JSON：配置文件格式。

## 配置文件

项目配置分为两类：

- `config/locations.de.json`：德国地区和城市配置。
- `config/app_config.json`：浏览器、引擎、停留时间、滚动策略、失败策略、导出路径等运行配置。

## 采集核心逻辑

当前核心采集能力已拆成三个层次：

- 浏览器层：`SeleniumBrowserEngine` 负责启动可视化 Chrome/Edge、打开搜索链接、等待语言无关的结果 DOM、滚动列表并获取运行时 HTML。
- 解析层：`parse_maps_list_results()` 负责从 Google Maps 搜索结果列表 DOM 中提取商家字段，字段不存在时保留空字符串。
- 服务层：`crawl_maps_search()` 负责执行单个搜索链接的“打开、滚动、解析、写入 SQLite”闭环。

等待 Google Maps 页面加载时不能依赖中文、英文或其他语言的可见文案，只能使用结构化 DOM 条件，例如 `div[role="feed"]`、`a[href*="/maps/place/"]` 或 `data-result-index`。

根目录下的 `keywords`、`keyword.txt`、`outputs/`、截图、HTML、CSV、数据库、缓存和临时诊断文件都属于本地运行产物，必须保持在 `.gitignore` 中，不进入 Git。

## 合规和边界

本软件只用于用户自行确认合规场景下的数据采集和自动化辅助。软件不得实现自动绕过验证码、登录限制、访问限制或其他风控机制的功能。遇到验证码、异常页面或疑似风控页面时，应暂停任务并等待人工处理。

Google Maps 相关服务可能有禁止抓取、批量保存或自动化访问的条款限制。正式使用前，使用者应自行确认使用方式符合目标网站和所在地区的法律、条款与政策要求。

## 文档维护规则

每次开发、修改或调试后，必须同步检查并更新相关文档：

- 功能变化：更新 `docs/REQUIREMENTS.md`。
- 技术实现变化：更新 `docs/DESIGN.md`。
- 目录或文件变化：更新 `docs/PROJECT_STRUCTURE.md`。
- 运行方式变化：更新 `README.md`。
- 开发流程变化：更新 `docs/DEVELOPMENT_WORKFLOW.md`。
- 版本变化：更新 `CHANGELOG.md`。
- 面向智能体的规则变化：更新 `AGENTS.md`。

文档必须和代码保持一致，不允许文档描述已经失效的代码结构或功能。

## 开发环境

本项目使用 Anaconda 管理开发环境。

环境要求：

- Conda 环境名称：`gmap`
- Python 版本：优先使用 Python 3.11，以兼容 PySide6、PySide6-Fluent-Widgets、Selenium、Playwright、pandas 等依赖。
- pip 镜像源：优先使用清华源 `https://pypi.tuna.tsinghua.edu.cn/simple`
- 浏览器驱动、Playwright 浏览器缓存和其他开发工具尽量放在当前项目目录下，便于后续整体迁移。

当前开发环境创建在项目内：

```text
.conda/gmap
```

常用命令：

```powershell
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m pytest tests/unit -v
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m gmap_collector.main --check
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m gmap_collector.main
```

依赖文件：

- `environment.yml`：Conda 环境定义。
- `requirements.txt`：Python 依赖及版本。
- `pyproject.toml`：Python 包元数据，用于把 `src/` 布局项目安装为可编辑包。
- `pytest.ini`：测试配置，指定测试目录和源码导入路径。

后续安装命令以实际开发阶段文档为准。

## Git 开发与提交规范

本项目统一使用 Git 管理全部开发过程。每一次功能开发、问题修复、文档调整、配置变更和依赖更新，都必须通过 Git 提交记录保存，便于追踪、回滚和协作。

### 基本原则

- 所有提交说明统一使用中文。
- 每次提交只做一类清晰变更，避免把无关修改混在一起。
- 提交前必须先运行必要验证。
- 修改代码时必须同步更新相关文档。
- 不提交本地环境、缓存、数据库、日志、导出文件、浏览器缓存和个人编辑器配置。
- 不提交 Token、Cookie、账号、代理、私有商家数据等敏感信息。

### 推荐开发流程

1. 开始开发前，确认当前分支和工作区状态。

```powershell
& 'D:\Git\cmd\git.exe' status --short --branch
```

2. 拉取远程最新代码。

```powershell
& 'D:\Git\cmd\git.exe' pull --ff-only
```

3. 开发或修改功能。

4. 运行测试和基础检查。

```powershell
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m pytest tests/unit -v
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m gmap_collector.main --check
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m pip check
```

5. 检查变更范围。

```powershell
& 'D:\Git\cmd\git.exe' status --short
& 'D:\Git\cmd\git.exe' diff
```

6. 暂存文件。

```powershell
& 'D:\Git\cmd\git.exe' add .
```

7. 提交变更。

```powershell
& 'D:\Git\cmd\git.exe' commit -m "类型: 简短中文说明"
```

8. 推送到 GitHub。

```powershell
& 'D:\Git\cmd\git.exe' push
```

### 提交信息格式

提交信息统一使用：

```text
类型: 简短中文说明
```

示例：

```text
功能: 添加关键词任务生成逻辑
修复: 修正来源关键词去重规则
文档: 更新 Git 提交流程说明
测试: 添加 SQLite 仓储测试
配置: 调整 Playwright 浏览器缓存路径
重构: 拆分浏览器引擎接口
```

### 提交类型

| 类型 | 使用场景 |
| --- | --- |
| 功能 | 新增用户可见功能或核心能力 |
| 修复 | 修复 bug、异常或错误行为 |
| 文档 | 修改 README、AGENTS、docs、注释说明等 |
| 测试 | 新增或修改测试 |
| 配置 | 修改依赖、环境、配置文件、GitHub 模板等 |
| 重构 | 不改变功能行为的代码结构调整 |
| 样式 | 仅调整界面样式、格式或展示细节 |
| 构建 | 修改打包、构建、发布相关内容 |
| 清理 | 删除无用文件、缓存、过时代码或整理目录 |

### 回滚方式

如果某次提交引入问题，优先使用 `revert` 创建反向提交，保留历史记录：

```powershell
& 'D:\Git\cmd\git.exe' revert <提交ID>
```

不建议随意使用会改写历史的命令，例如：

```powershell
git reset --hard
git push --force
```

除非已经明确知道影响，并且确认不会破坏远程仓库或他人工作。

### 文档同步要求

每次提交前必须检查文档是否需要同步更新：

- 功能变化：更新 `docs/REQUIREMENTS.md`
- 技术设计变化：更新 `docs/DESIGN.md`
- 目录结构变化：更新 `docs/PROJECT_STRUCTURE.md`
- 开发流程变化：更新 `docs/DEVELOPMENT_WORKFLOW.md`
- 用户使用方式变化：更新 `README.md`
- 版本或重要阶段变化：更新 `CHANGELOG.md`
- 智能体规则变化：更新 `AGENTS.md`

### 发布前检查

公开发布或阶段性版本提交前，至少执行：

```powershell
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m pytest tests/unit -v
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m gmap_collector.main --check
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m pip check
& 'D:\Git\cmd\git.exe' status --short --branch
```

确认测试通过、GUI 可初始化、依赖无冲突、工作区干净后，再推送到 GitHub。

## GUI 组件库约束

第一版前端界面使用 `PySide6-Fluent-Widgets` 构建。该库基于 PySide6，安装包名为 `PySide6-Fluent-Widgets`，代码导入包名通常为 `qfluentwidgets`。

注意事项：

- 不使用纯 Tkinter。
- 不使用 PyQt 版本的 Fluent Widgets。
- 不同时安装 PyQt-Fluent-Widgets、PySide2-Fluent-Widgets 等同名导入包，避免 `qfluentwidgets` 包名冲突。
- GUI 页面应优先使用该库提供的导航、按钮、输入框、表格、信息提示和主题组件。
