# 技术设计

本文档记录项目第一版技术设计。后续技术路线、架构边界、数据库结构、配置结构或模块职责发生变化时，必须同步更新本文档。

## 一、总体架构

项目采用分层架构：

```text
GUI 层
  ↓
任务调度层
  ↓
浏览器引擎层
  ↓
页面解析层
  ↓
存储层
  ↓
导出层
```

配置、日志、通用工具作为横向基础模块被各层使用。

## 二、技术栈

| 类型 | 选型 | 说明 |
| --- | --- | --- |
| 开发语言 | Python | 整个项目使用 Python |
| 环境管理 | Anaconda | Conda 环境名称固定为 `gmap` |
| GUI 基础框架 | PySide6 | 桌面界面基础框架 |
| GUI 组件库 | PySide6-Fluent-Widgets | Fluent 风格组件库，导入包名通常为 `qfluentwidgets` |
| 本地数据库 | SQLite | 便于打包和目录迁移 |
| 浏览器自动化 | Selenium | 第一浏览器引擎 |
| 浏览器自动化 | Playwright | 第二浏览器引擎，可插拔扩展 |
| 配置格式 | JSON | 适合层级地区配置 |
| 导出 | pandas / openpyxl | CSV 和 Excel 导出 |

Python 版本优先选择 3.11。该版本对 PySide6、PySide6-Fluent-Widgets、Selenium、Playwright、pandas 和 openpyxl 有较好的兼容性。

## 三、模块边界

### GUI 层

负责：

- 页面展示。
- 用户输入。
- 按钮事件。
- 表格刷新。
- 状态展示。
- 日志展示。
- Fluent 风格组件组织。
- 主题、导航和常用控件样式。

不负责：

- 直接操作浏览器 DOM。
- 直接写 SQLite。
- 直接解析 Google Maps 页面。

GUI 层必须优先使用 `PySide6-Fluent-Widgets` 提供的组件。底层仍基于 PySide6，但不应退回到纯 Tkinter 或其他 GUI 框架。

### 任务调度层

负责：

- 任务创建。
- 关键词队列管理。
- 任务状态流转。
- 暂停和继续。
- 停止。
- 失败重试。
- 连续失败计数。
- 保存和读取任务运行参数快照。

当前实现：

- `TaskRepository` 负责 SQLite 中的批次、关键词任务、失败重试和最近可恢复批次查询。
- `TaskRunner` 负责单线程顺序执行一个批次，并在当前关键词完成后响应暂停或停止请求。
- `TaskWorker` 作为 GUI 后台线程，负责把任务调度层、Selenium 浏览器引擎和采集服务串联起来。
- `WebsiteExplorationRepository` 负责从某个 Google Maps 批次创建官网探索批次，并维护官网探索任务状态。
- `WebsiteExplorationWorker` 作为 GUI 后台线程，负责顺序执行官网探索任务，并在静态请求失败或无核心联系方式时调用 Selenium 浏览器兜底。

### 浏览器引擎层

负责：

- 启动 Chrome 或 Edge。
- 按配置选择 Selenium 或 Playwright。
- 打开 URL。
- 等待页面加载。
- 等待普通网页 DOM ready。
- 滚动搜索结果列表。
- 提供页面 DOM 给解析层。
- 检测异常页面并返回状态。

Selenium 和 Playwright 必须实现统一接口，避免业务代码依赖具体引擎。

### 页面解析层

负责：

- 识别搜索结果列表中的商家卡片。
- 解析商家名称、地址、电话、官网、评分、评论数量、商家分类、Google Maps 链接。
- 对解析失败的字段返回空值。
- 不点击商家详情页。
- 从商家官网 HTML 中提取电话、邮箱、Instagram、TikTok、Twitter / X、Facebook、LinkedIn、YouTube、WhatsApp 和 SEO Keywords。

### 存储层

负责：

- 初始化 SQLite 表。
- 保存任务批次。
- 保存关键词任务。
- 保存商家记录。
- 按 Google Maps 链接去重。
- 合并来源关键词。
- 查询任务状态。
- 查询导出数据。
- 保存官网探索批次。
- 保存官网探索任务。
- 标记官网探索任务为待执行、完成、失败或跳过。
- 将官网探索结果写回商家主表，供结果管理页和导出模块统一读取。

### 导出层

负责：

- 从 SQLite 查询去重后的商家记录。
- 导出 CSV。
- 导出 Excel。
- 生成导出文件名。

### 配置层

负责：

- 读取地区配置。
- 读取运行配置。
- 校验配置字段。
- 提供默认配置。
- 保存 GUI 修改后的运行配置。

### 日志层

负责：

- 写入运行日志。
- 写入错误日志。
- 向 GUI 发送日志消息。

## 四、数据模型草案

### task_batches

任务批次表。

| 字段 | 说明 |
| --- | --- |
| id | 主键 |
| name | 批次名称 |
| status | 批次状态 |
| total_keywords | 总关键词数 |
| completed_keywords | 已完成数量 |
| failed_keywords | 失败数量 |
| runtime_config | 本次任务运行参数快照，JSON 字符串 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

### keyword_tasks

关键词任务表。

| 字段 | 说明 |
| --- | --- |
| id | 主键 |
| batch_id | 所属批次 |
| keyword | 行业关键词 |
| country_name | 国家显示名 |
| country_search_name | 国家搜索名 |
| region_name | 地区显示名 |
| region_search_name | 地区搜索名 |
| city_name | 城市显示名 |
| city_search_name | 城市搜索名 |
| query_text | 完整搜索词 |
| search_url | Google Maps 搜索链接 |
| status | 待执行、执行中、完成、失败、已跳过 |
| failure_reason | 失败原因 |
| last_run_at | 最后执行时间 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

### businesses

商家主记录表。

| 字段 | 说明 |
| --- | --- |
| id | 主键 |
| name | 商家名称 |
| address | 地址 |
| phone | 电话 |
| explored_phone | 官网探索二次提取的新电话 |
| emails | 官网探索提取的邮箱 |
| instagram | 官网探索提取的 Instagram |
| tiktok | 官网探索提取的 TikTok |
| twitter_x | 官网探索提取的 Twitter / X |
| facebook | 官网探索提取的 Facebook |
| linkedin | 官网探索提取的 LinkedIn |
| youtube | 官网探索提取的 YouTube |
| whatsapp | 官网探索提取的 WhatsApp |
| seo_keywords | 官网首页 SEO Keywords |
| website_exploration_status | 官网探索状态 |
| website_explored_at | 官网探索时间 |
| website | 官网 |
| rating | 评分 |
| review_count | 评论数量 |
| category | 商家分类 |
| google_maps_url | Google Maps 链接，唯一 |
| source_keywords | 来源行业关键词，英文逗号分隔 |
| first_seen_at | 首次采集时间 |
| last_seen_at | 最后采集时间 |

### business_task_hits

商家命中记录表。

| 字段 | 说明 |
| --- | --- |
| id | 主键 |
| business_id | 商家 ID |
| keyword_task_id | 关键词任务 ID |
| query_text | 完整搜索词 |
| created_at | 创建时间 |

该表用于追踪某个商家是由哪些关键词任务命中的，便于后续审计和扩展。

说明：`businesses.source_keywords` 只保存用户输入的行业关键词，例如 `Car Wrap Shop,PPF`。完整搜索词包含城市、地区和逗号，统一保存在 `business_task_hits.query_text`，避免逗号分隔字段产生歧义。

### website_exploration_batches

官网探索批次表。

| 字段 | 说明 |
| --- | --- |
| id | 主键 |
| source_batch_id | 来源 Google Maps 批次 ID |
| name | 批次名称 |
| status | 批次状态 |
| total_businesses | 总商家数 |
| completed_businesses | 已完成数 |
| failed_businesses | 失败数 |
| skipped_businesses | 跳过数 |
| runtime_config | 官网探索运行参数快照 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

### website_exploration_tasks

官网探索任务表。

| 字段 | 说明 |
| --- | --- |
| id | 主键 |
| batch_id | 所属官网探索批次 |
| business_id | 来源商家 ID |
| business_name | 商家名称 |
| website_url | 商家官网 |
| status | 待执行、执行中、完成、失败、跳过 |
| failure_reason | 失败或跳过原因 |
| last_run_at | 最后执行时间 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

## 五、任务状态流转

关键词任务状态：

```text
待执行 -> 执行中 -> 完成
待执行 -> 执行中 -> 失败
失败 -> 待执行
待执行 -> 已跳过
```

当前代码状态值使用英文写入 SQLite：

- `pending`：待执行。
- `running`：执行中。
- `success`：完成。
- `failed`：失败。

批次任务状态：

```text
未开始 -> 执行中 -> 暂停
执行中 -> 完成
执行中 -> 停止
执行中 -> 暂停
暂停 -> 执行中
```

当前代码状态值使用英文写入 SQLite：

- `pending`：未开始或仍有待执行关键词。
- `running`：执行中。
- `paused`：暂停。
- `stopped`：停止。
- `completed`：全部完成且无失败。
- `completed_with_errors`：已执行完但存在失败关键词。

连续失败达到阈值时，批次状态变为暂停。

任务配置页的运行参数会在创建批次时写入 `task_batches.runtime_config`。后续继续、恢复和重试时优先读取该快照，避免全局设置变更影响已经创建的任务。

## 六、滚动完成条件

单个关键词满足以下任一条件时判定完成：

1. Google Maps 搜索结果列表到达底部。
2. 连续 N 次滚动后没有新增商家。
3. 达到最大滚动次数。

其中 N 和最大滚动次数来自 `config/app_config.json`。

## 七、GUI 设计

第一版采用左侧侧边导航：

- 任务配置。
- 任务执行。
- 官网探索。
- 结果管理。
- 设置。

GUI 组件库使用 `PySide6-Fluent-Widgets`。页面应采用工具型桌面软件布局，优先保证信息密度、可读性和稳定性，不做营销页风格界面。

左侧导航负责页面切换，右侧主内容区承载当前页面。设置入口固定在左侧导航底部。主窗口默认尺寸为 `1180 x 760`，最小尺寸为 `1100 x 720`，左侧导航展开宽度为 `220`。后续增加模块时，应优先通过新增导航项扩展，不创建多个主窗口。

GUI 页面应优先使用 Fluent 卡片、设置卡片、表格、搜索框、按钮、滚动区和进度条。任务参数数字输入框使用防滚轮误触控件，避免用户滚动页面时意外修改运行参数。

### 任务配置

该页面用于选择地区、输入关键词、设置运行参数并生成任务预览。

主要区域：

- 国家和地区卡片。
- 行业关键词卡片。
- 本次任务参数卡片。
- 任务预览表格卡片。

国家和地区卡片中的地区复选框必须放入独立 Fluent 滚动区域。地区数量很多时，只滚动该局部区域，不允许撑长整个任务配置页面；地区数量很少时，复选框行高保持固定，多余空间由底部弹性区占用。

### 任务执行

该页面用于控制采集任务。

主要区域：

- 任务控制按钮。
- 状态统计，包含运行状态、当前关键词、国家、地区、城市、浏览器引擎、原始命中数量和去重商家数量。
- 关键词队列表格。
- 运行日志。

点击开始后，主窗口会在后台浏览器真正启动前调用任务执行页的启动状态刷新方法，立即展示“启动中”、不确定进度条和下一条待执行关键词信息。后台任务线程在每个关键词刚进入运行状态时再次发出刷新信号，确保状态面板和关键词队列表同步更新。

### 结果管理

该页面用于查看、筛选和导出商家记录。

主要区域：

- 结果筛选卡片。
- 商家结果表格卡片。
- 详情卡片。

结果管理页是基础采集结果和官网探索结果的统一汇总视图，因此表格字段不仅包括 Google Maps 原始字段，也包括官网探索新增字段：

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

### 官网探索

该页面负责官网二次任务的创建和管理。

主要区域：

- 来源任务选择卡片。
- 官网探索批次卡片。
- 官网探索任务卡片。
- 探索日志卡片。

当前已完成：

- 从某个 Google Maps 批次读取来源商家。
- 按商家去重创建官网探索任务。
- 无官网商家自动跳过。
- 按来源 Task 过滤官网探索批次，一个来源 Task 可以创建多个探索批次。
- 配置探索深度、每站最多页面数和请求超时秒数。
- 展示运行状态、总商家数、已完成、失败、跳过、待探索、当前商家和当前官网。
- 静态抓取同主域及其子域页面。
- 正则提取电话、邮箱、社媒链接和 SEO Keywords。
- 静态请求失败、超时或无核心联系方式时，使用 Selenium 浏览器兜底获取页面 HTML。
- 将官网探索结果写回商家主表，并在结果管理页统一查看和导出。

### 设置

该页面用于管理外观、全局默认运行参数、项目路径和维护操作，不展示项目开发文档入口。

主要区域：

- 外观设置卡片组：支持跟随系统、亮色、暗色主题。
- 全局运行设置卡片组：展示默认浏览器、默认自动化引擎、页面停留、关键词停留、滚动停留、最大滚动次数、连续无新增停止次数、页面加载超时和连续失败暂停阈值。
- 项目路径卡片组：展示配置文件、地区配置、SQLite 数据库、导出目录、日志目录、Selenium 缓存目录和 Playwright 浏览器目录。
- 维护卡片组：提供清空数据库和缓存按钮。

该页面还提供 `清空数据库和缓存` 维护按钮。该按钮属于危险操作，执行前必须弹出二次确认。用户确认后，主窗口调用运行产物清理服务，清理 SQLite 数据库、日志、导出文件、调试输出、截图和 `drivers/selenium-cache/` 浏览器用户缓存；配置文件、源码和关键词文件不被删除。清理完成后，主窗口会重新初始化 SQLite 表结构，清空当前批次状态，并刷新任务执行页和结果管理页。

## 八、浏览器引擎接口设计

浏览器引擎应提供统一能力：

- 启动浏览器。
- 关闭浏览器。
- 打开 URL。
- 等待页面加载。
- 滚动结果列表。
- 获取当前已加载商家 DOM。
- 判断是否到达列表底部。
- 判断是否出现异常页面。

业务代码只依赖统一接口，不直接依赖 Selenium 或 Playwright。

当前第一版只有 Selenium 具备真实执行能力。Playwright 引擎保留接口和配置入口，但尚未实现 Google Maps 列表滚动与 DOM 采集；GUI 在选择 Playwright 启动任务时会提示暂不支持。

官网探索使用两阶段抓取策略：

1. 静态请求阶段：使用标准库 HTTP 请求访问官网，按探索深度和每站最多页面数遍历同主域及其子域页面，不访问外部普通页面。
2. 浏览器兜底阶段：如果静态请求失败、超时或没有提取到邮箱、电话、社媒等核心联系方式，则按需启动 Selenium 浏览器打开官网，等待普通网页 DOM ready 后获取页面 HTML，再复用同一解析器提取字段。

官网探索中的静态请求和浏览器兜底都必须受请求超时配置约束。单个官网失败后只标记当前官网探索任务失败，不允许阻塞整个批次。静态请求失败但浏览器兜底成功时，最终状态按成功统计，保证前端状态、任务统计和数据库结果一致。

`scripts.open_login_browser` 不通过 Selenium WebDriver 打开登录页，而是直接启动系统安装的真实浏览器进程。Chrome 默认优先使用安装目录中的 `chrome_proxy.exe`，并通过 `--user-data-dir=drivers/selenium-cache/<browser>` 把登录缓存写入项目目录。该目录与正式 Selenium 采集任务一致，因此登录状态可被后续采集复用，同时降低 Google 登录阶段出现 `This browser or app may not be secure` 的概率。

`scripts.cleanup_runtime_data` 默认只清理本地运行数据库、日志、导出、调试输出和截图，不清理关键词输入、配置文件和 `drivers/selenium-cache/` 浏览器登录缓存。传入 `--include-browser-cache` 或由 GUI 设置页清理按钮调用时，会同步删除 `drivers/selenium-cache/`。Windows 下如果 SQLite 文件被当前 GUI 进程占用，GUI 清理流程会清空业务表并重置自增序列作为兜底；清空范围包含 Google Maps 任务、商家、命中关系、官网探索批次和官网探索任务，确保软件回到空数据状态。

## 九、异常处理设计

异常类型包括：

- 浏览器启动失败。
- 页面加载超时。
- 结果列表定位失败。
- DOM 解析失败。
- 网络异常。
- 验证码或异常页面。
- 数据库写入失败。
- 导出失败。

处理原则：

- 单个关键词失败时记录失败原因并继续下一个关键词。
- 连续失败达到阈值时暂停整个批次。
- 验证码或疑似风控页面出现时暂停任务并等待人工处理。
- 无法解释的问题必须询问用户。

## 十、合规设计

软件不实现以下能力：

- 自动绕过验证码。
- 自动登录或维护账号池。
- 自动切换代理绕过访问限制。
- 强行突破网站限制。

遇到限制页面时，软件只暂停并提示人工处理。

## 十一、扩展点

后续可扩展：

- 更多国家配置。
- CSV/JSON 导入地区配置。
- 街道级搜索。
- 更多导出格式。
- 新浏览器引擎。
- 更精细的解析策略。
- 任务批次管理。
- 数据清洗规则。
- 安装器、代码签名和自动更新。

## 十二、开发环境和工具目录

开发环境要求：

- 使用 Anaconda 创建 `gmap` 环境。
- 依赖安装优先使用清华源。
- Python 依赖版本写入 `requirements.txt`。
- Conda 环境定义写入 `environment.yml`。

工具目录约定：

```text
drivers/
├── selenium-cache/
└── playwright-browsers/
```

说明：

- `drivers/selenium-cache/` 用于保存 Chrome/Edge 的项目内用户数据目录，主要包括登录态、Cookie、Profile 等可复用浏览器状态。
- `drivers/playwright-browsers/` 用于保存 Playwright 浏览器缓存。
- 这些目录放在项目内，便于后续整体迁移和打包。

## 十三、Windows 打包发布设计

Windows 发行版使用 PyInstaller onedir 模式生成，入口为 `src/gmap_collector/main.py`，产物名称为 `GoogleMaps_LeadForge.exe`。不采用单文件 exe，原因是 PySide6、qfluentwidgets 和浏览器自动化依赖较多，onedir 更便于排查缺失资源，也更适合保留可迁移的配置和运行目录。

打包后的项目根目录按 exe 所在目录计算。发布目录内必须包含：

```text
GoogleMaps_LeadForge.exe
config/
data/
exports/
logs/
drivers/
README.md
LICENSE
CHANGELOG.md
```

其中 `config/` 随包提供默认配置，`data/`、`exports/`、`logs/` 和 `drivers/` 作为运行目录在 exe 同级保留。用户迁移软件时整体复制发行版目录即可。发行版不内置 Google Chrome 或 Microsoft Edge，正式采集仍调用用户本机已安装的可视化浏览器。

源码构建 Windows 发行版时使用 `scripts/build_windows_release.ps1`。该脚本负责调用 PyInstaller、整理发布目录并生成 `dist/GoogleMaps_LeadForge-v<version>-windows-x64.zip`，不负责上传 GitHub Release。
