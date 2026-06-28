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
- 支持从某个 Google Maps 采集任务创建“官网探索”二次任务，进一步提取官网电话、邮箱、社媒和 SEO Keywords。
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

官网探索模块会从商家主记录中的官网字段发起二次采集，优先使用静态 HTTP 请求获取 HTML 并正则提取信息；当静态请求失败、超时或未提取到核心联系方式时，会使用 Selenium 浏览器打开官网作为兜底，再从运行时 DOM 中提取字段：

| 字段 | 说明 |
| --- | --- |
| 官网探索电话 | 从商家官网二次提取的新电话 |
| Email | 从商家官网提取的邮箱 |
| Instagram | 从商家官网提取的 Instagram 链接或账号 |
| TikTok | 从商家官网提取的 TikTok 链接或账号 |
| Twitter / X | 从商家官网提取的 Twitter 或 X 链接 |
| Facebook | 从商家官网提取的 Facebook 链接 |
| LinkedIn | 从商家官网提取的 LinkedIn 链接 |
| YouTube | 从商家官网提取的 YouTube 链接 |
| WhatsApp | 从商家官网提取的 WhatsApp 链接或号码 |
| SEO Keywords | 官网首页 SEO Keywords |
| 官网探索状态 | 未探索、待执行、运行中、完成、失败或跳过 |
| 官网探索时间 | 最近一次官网探索完成时间 |

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

这些功能可以作为后续版本扩展，但必须先确认需求边界和设计方案；功能经用户验收后，再正式同步需求文档和设计文档并提交。

## 基本工作流

1. 启动软件。
2. 软件读取 `config/locations.json` 和 `config/app_config.json`。
3. 在“任务配置”页选择国家和地区。
4. 在关键词输入框中输入行业关键词，一行一个。
5. 生成任务预览。
6. 创建任务并进入“任务执行”页。
7. 点击开始，软件打开可视化浏览器窗口并顺序访问 Google Maps 搜索链接。
8. 每个关键词页面持续滚动加载列表结果。
9. 达到列表底部，或连续多次滚动没有新增商家时，该关键词标记为完成。
10. 解析到的商家记录写入 SQLite，并按 Google Maps 链接去重。
11. 任务可手动暂停、继续、停止。
12. 可在“官网探索”页从某个 Google Maps 任务创建官网探索批次；无官网商家会直接标记为跳过。
13. 官网探索按任务批次执行，支持请求超时、每站最多页面数、探索深度和浏览器兜底。
14. 任务完成后在“结果管理”页按 Task 查看基础字段和官网探索字段，并导出 CSV 或 Excel。

## 页面设计

第一版使用左侧侧边导航组织页面：

- 任务配置
- 任务执行
- 官网探索
- 结果管理
- 设置

左侧导航使用 `PySide6-Fluent-Widgets` 的导航组件实现。主窗口左侧固定显示页面入口，右侧显示当前页面内容；设置入口固定在左侧导航底部。默认窗口尺寸为 `1180 x 760`，最小尺寸为 `1100 x 720`，左侧导航展开宽度为 `220`，避免默认界面占用过多屏幕空间。

页面自适应规则：

- 主窗口设置默认尺寸和最小尺寸，避免窗口过大或被缩到控件无法排版的状态。
- 每个功能页面使用 Fluent `ScrollArea` 页面级滚动区域，窗口变矮时优先滚动内容，而不是裁剪底部按钮。
- 关键操作按钮放在固定操作栏中，例如“创建任务并进入执行页”和“保存全局设置”。
- 表格统一使用 Fluent `TableWidget`，支持默认列宽、手动拖拽、长列拉伸和平滑滚动。
- 文本框、日志区和卡片设置最小高度和可扩展策略，缩放窗口时优先压缩空白区域，不让文字只显示一半。
- 数字输入框使用防滚轮误触控件，滚动页面时不会意外修改运行参数。

### 任务配置页

任务配置页由 Fluent 卡片组织，包含国家地区、行业关键词、本次任务参数和任务预览。

国家和地区卡片：

- 国家列表。
- 地区/州复选框，放在独立的局部滚动区域中，地区很多时不撑长整个页面。
- 地区较少时，复选框保持固定正常行高，多余空间留在列表底部。
- `全选地区` 按钮。
- `取消全选` 按钮。
- `刷新配置` 按钮。

行业关键词卡片：

- 多行文本框，一行一个关键词。
- 预计生成任务数。
- `生成任务预览` 按钮。
- `清空关键词` 按钮。

本次任务参数卡片：

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
- 本次任务快照会保存到 SQLite 的任务批次记录中；软件重启后恢复任务时继续使用该快照。

任务预览卡片：

- 序号。
- 行业关键词。
- 城市。
- 地区。
- 国家。
- 生成的 Google Maps 链接。
- `创建任务并进入执行页` 按钮。

### 任务执行页

任务执行页由任务运行状态、关键词队列、运行日志和底部控制栏组成。任务启动或运行中会显示不确定进度条，便于确认程序正在执行。

任务执行页以 Task 为基本单位运行。页面顶部提供当前任务选择器，用户可以选择要执行的任务批次；任务运行中会锁定任务选择器和关键按钮，避免后台实际运行任务与前端显示状态不一致。

底部控制栏：

- `开始`
- `暂停`
- `继续`
- `停止`
- `重试失败关键词`
- `导出结果`

任务运行状态卡片：

- 运行状态。
- 总关键词数。
- 已完成数量。
- 失败数量。
- 待执行数量。
- 已采集商家数。
- 去重后商家数。
- 连续失败次数。
- 当前关键词。
- 当前国家。
- 当前地区。
- 当前城市。
- 当前浏览器引擎。

关键词队列表格：

- 状态。
- 行业关键词。
- 城市。
- 地区。
- 国家。
- 失败原因。
- 最后执行时间。

运行日志卡片：

- 启动浏览器日志。
- 打开链接日志。
- 滚动加载日志。
- 本轮解析数量。
- 失败原因。
- 暂停原因。

### 结果管理页

结果管理页由结果筛选、商家结果和详情卡片组成，是 Google Maps 基础采集和官网探索结果的最终汇总视图。

结果筛选卡片：

- 当前任务选择器。
- 按关键词筛选。
- 按地区、城市或商家分类筛选。
- `刷新数据` 按钮。
- `导出 CSV` 按钮。
- `导出 Excel` 按钮。

商家结果表格：

- 商家名称。
- 地址。
- 电话。
- 官网探索电话。
- Email。
- Instagram。
- TikTok。
- Twitter / X。
- Facebook。
- LinkedIn。
- YouTube。
- WhatsApp。
- SEO Keywords。
- 官网探索状态。
- 官网探索时间。
- 官网。
- 评分。
- 评论数量。
- 商家分类。
- Google Maps 链接。
- 来源关键词。
- 首次采集时间。
- 最后更新时间。

详情卡片：

- 完整 Google Maps 链接。
- 来源关键词列表。
- 采集任务信息。

### 官网探索页

官网探索页用于管理二次采集任务。当前已完成任务创建、静态抓取、正则提取、浏览器兜底和结果写回：

- 从已有 Google Maps 任务批次选择来源。
- 创建官网探索批次。
- 有官网商家进入待执行队列。
- 无官网商家直接标记为跳过。
- 一个来源任务可以创建多个官网探索批次，批次列表按当前来源任务过滤展示。
- 支持配置探索深度、每站最多页面数和请求超时秒数。
- 优先通过静态请求抓取官网 HTML，按正则提取电话、邮箱、社媒和 SEO Keywords。
- 静态请求失败、超时或未提取到核心联系方式时，使用 Selenium 浏览器兜底获取页面 HTML。
- 展示当前探索批次的运行状态、总商家数、已完成、失败、跳过、待探索、当前商家和当前官网。
- 将探索结果写回商家主表，并在结果管理页统一展示和导出。

### 设置页

该页面用于集中管理外观、基础全局设置、关键路径和维护操作。项目文档不在软件设置页中展示，避免把开发文档混入用户配置页面。

外观设置包括：

- 颜色方案：跟随系统、亮色、暗色。

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
- `config/locations.json`
- SQLite 数据库路径。
- 导出目录。
- 日志目录。
- Selenium 缓存目录。
- Playwright 浏览器目录。

维护操作包括：

- `清空数据库和缓存`：清理 SQLite 数据库、日志、导出文件、调试输出、截图和浏览器用户缓存。该操作会弹出二次确认；确认后会让项目回到接近全新运行状态，但不会删除源码、配置文件或 `keyword.txt`。

主要表格使用“默认列宽 + 手动拖拽 + 长列拉伸”的混合策略：

- 国家、地区、城市、关键词等常用列提供更宽的默认宽度。
- 表头允许用户手动拖拽调整列宽，便于临时查看长文本。
- Google Maps 链接、失败原因等长文本列使用拉伸列承接剩余空间。
- 使用 Fluent 平滑滚动机制，后续数据量增大时仍然可以滚动查看。

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

- `config/locations.json`：全国家地区和城市配置。
- `config/app_config.json`：浏览器、引擎、停留时间、滚动策略、失败策略、导出路径等运行配置。

如果需要根据本地原始数据重新生成全国家地区配置，可以执行：

```powershell
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m scripts.generate_locations_config --country-table tests\guojia\guojia2.html --cities tests\json-cities\cities.json --output config\locations.json
```

生成脚本默认导入 `city`、`town`、`capital`、`municipality`、`locality` 等适合搜索的地点类型；如果某个国家没有这些类型，会使用该国家现有行政数据兜底，避免国家从配置中丢失。

`tests/guojia/` 和 `tests/json-cities/` 是本地原始数据目录，只用于重新生成配置，不提交到 Git。

## 采集核心逻辑

当前核心采集能力已拆成三个层次：

- 浏览器层：`SeleniumBrowserEngine` 负责启动可视化 Chrome/Edge、打开搜索链接、等待语言无关的结果 DOM、滚动列表并获取运行时 HTML。
- 解析层：`parse_maps_list_results()` 负责从 Google Maps 搜索结果列表 DOM 中提取商家字段，字段不存在时保留空字符串。
- 服务层：`crawl_maps_search()` 负责执行单个搜索链接的“打开、滚动、解析、写入 SQLite”闭环。
- 任务层：`TaskRepository` 和 `TaskRunner` 负责创建批次、保存运行参数快照、顺序执行关键词、暂停/继续/停止、失败重试和连续失败自动暂停。
- GUI 执行层：`TaskWorker` 在独立线程中驱动 Selenium，避免采集时卡住主界面。
- 官网探索任务层：`WebsiteExplorationRepository` 负责从 Google Maps 批次创建官网探索批次，并维护有官网、无官网、待执行、完成、失败和跳过等状态。
- 官网探索抓取层：`website_crawler.py` 负责静态遍历同主域页面；`website_info_parser.py` 负责正则提取电话、邮箱、社媒和 SEO Keywords；`WebsiteExplorationWorker` 在静态采集失败时按需启动 Selenium 浏览器兜底。

当前 GUI 已支持从任务预览创建 SQLite 批次、进入任务执行页、启动/暂停/继续/停止当前批次、重试失败关键词、刷新结果和导出 CSV/Excel。

当前官网探索模块已完成从指定 Google Maps 批次读取命中商家、按商家去重创建官网探索任务、无官网自动跳过、静态请求抓取、正则提取、浏览器兜底、结果写回和状态统计刷新。

任务执行页会展示当前运行状态、当前关键词、国家、地区、城市、浏览器引擎、原始命中数量和去重商家数量。点击开始后，界面会先显示“启动中”，避免浏览器启动期间没有反馈。

当前第一版实际执行采集时只落地 Selenium。Playwright 作为后续扩展入口保留在配置和界面中；如果当前版本选择 Playwright 启动任务，软件会提示暂不支持，不会静默改用其他引擎。

如果需要先登录 Google 账户，可以使用真实 Chrome 进程打开登录页，并把登录缓存写入采集任务复用的用户目录。该脚本默认优先启动系统 Chrome 安装目录下的 `chrome_proxy.exe`，避免登录阶段通过 Selenium WebDriver 打开浏览器导致 Google 提示 `This browser or app may not be secure`：

```powershell
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m scripts.open_login_browser --browser chrome
```

登录缓存目录固定为：

```text
D:\WorkSpace\Python\GMap\drivers\selenium-cache\chrome
```

如果需要手动指定 Chrome 启动器路径，可以执行：

```powershell
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m scripts.open_login_browser --browser chrome --executable 'C:\Program Files\Google\Chrome\Application\chrome_proxy.exe'
```

如果 `chrome_proxy.exe` 在当前电脑上表现异常，可以改用普通 `chrome.exe`：

```powershell
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m scripts.open_login_browser --browser chrome --no-chrome-proxy
```

清理本地运行产物可以执行：

```powershell
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m scripts.cleanup_runtime_data
```

默认清理脚本会删除 `data/app.sqlite3`、日志、导出、调试输出和截图等运行产物，但不会删除 `keyword.txt`、配置文件或 `drivers/selenium-cache/` 浏览器登录缓存。清理范围包含 Google Maps 任务表、商家表、命中关系表、官网探索批次表和官网探索任务表。

如果需要同时清理浏览器登录缓存，让项目回到更干净的测试状态，可以执行：

```powershell
& 'D:\WorkSpace\Python\GMap\.conda\gmap\python.exe' -m scripts.cleanup_runtime_data --include-browser-cache
```

在 GUI 的“设置”页，也可以点击 `清空数据库和缓存` 按钮完成同类清理。该按钮会二次确认，并且在 Windows 下数据库文件被当前程序占用时，会清空 SQLite 业务表作为兜底。

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

5. 提供启动命令，让用户自行启动软件并进行功能验收。用户未确认前，不进行最终文档落地和 Git 提交；除非用户明确要求，开发者或智能体不主动启动 GUI。

6. 用户确认功能无误后，同步更新 README、AGENTS、docs、CHANGELOG 和项目结构说明等相关文档。

7. 检查变更范围。

```powershell
& 'D:\Git\cmd\git.exe' status --short
& 'D:\Git\cmd\git.exe' diff
```

8. 暂存文件。

```powershell
& 'D:\Git\cmd\git.exe' add .
```

9. 提交变更。

```powershell
& 'D:\Git\cmd\git.exe' commit -m "类型: 简短中文说明"
```

10. 推送到 GitHub。

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
