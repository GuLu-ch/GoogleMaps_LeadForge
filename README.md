# GoogleMaps_LeadForge

GoogleMaps_LeadForge 是一个基于 Python 的桌面工具，用于通过 Google Maps 关键词搜索批量发现、采集、探索和导出商家线索数据。

本项目不是 Google 官方产品，也未获得 Google 赞助、认可或背书。使用者需要自行确认使用方式符合目标网站条款、当地法律法规和数据合规要求。

## 功能概览

- 根据国家、地区、城市和行业关键词批量生成 Google Maps 搜索任务。
- 使用可视化浏览器窗口顺序采集 Google Maps 搜索结果列表。
- 以 Task 为基本单位管理任务创建、任务执行、官网探索和结果导出。
- 使用 SQLite 保存任务、关键词状态、商家记录和官网探索结果。
- 按 Google Maps 链接去重，同一商家被多个关键词命中时合并来源关键词。
- 支持暂停、继续、停止、失败重试和连续失败自动暂停。
- 支持从商家官网进一步探索电话、Email、社交媒体和 SEO Keywords。
- 支持按任务查看结果，并导出 CSV 和 Excel。
- 支持 Chrome 和 Edge，默认优先使用 Chrome。

## 采集与导出字段

Google Maps 基础字段：

| 字段 | 说明 |
| --- | --- |
| 商家名称 | Google Maps 搜索结果中显示的商家名称 |
| 地址 | 搜索结果列表中可解析到的地址 |
| 电话 | 搜索结果列表中可解析到的电话 |
| 官网 | 搜索结果列表中可解析到的官网 |
| 评分 | 商家评分 |
| 评论数量 | 商家评论数量 |
| 商家分类 | Google Maps 显示的行业分类 |
| Google Maps 链接 | 商家去重使用的主键字段 |
| 来源关键词 | 命中该商家的行业关键词，多个关键词用英文逗号分隔 |

官网探索字段：

| 字段 | 说明 |
| --- | --- |
| 官网探索电话 | 从商家官网二次提取的新电话 |
| Email | 从商家官网提取的邮箱 |
| Instagram | Instagram 链接或账号 |
| TikTok | TikTok 链接或账号 |
| Twitter / X | Twitter 或 X 链接 |
| Facebook | Facebook 链接 |
| LinkedIn | LinkedIn 链接 |
| YouTube | YouTube 链接 |
| WhatsApp | WhatsApp 链接或号码 |
| SEO Keywords | 官网页面中的 SEO Keywords |
| 官网探索状态 | 未探索、待执行、运行中、完成、失败或跳过 |
| 官网探索时间 | 最近一次官网探索完成时间 |

## 环境要求

- Windows 系统。
- Anaconda 或 Miniconda。
- Python 3.11。
- Google Chrome，推荐优先安装。
- Microsoft Edge，可选。
- Git，可选，仅在需要从 GitHub 拉取源码时使用。

## 安装

从 GitHub 拉取项目：

```powershell
cd D:\WorkSpace\Python
git clone https://github.com/GuLu-ch/GoogleMaps_LeadForge.git
cd GoogleMaps_LeadForge
```

创建 Conda 环境：

```powershell
conda env create -f environment.yml
conda activate gmap
```

安装或更新 Python 依赖：

```powershell
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

如果使用项目内已经创建好的本地环境，也可以在项目根目录执行：

```powershell
& '.\.conda\gmap\python.exe' -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

如果后续需要使用 Playwright 浏览器能力，可以把浏览器下载到项目目录内：

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH="$PWD\drivers\playwright-browsers"
python -m playwright install chromium
```

## 启动软件

Conda 环境已激活时：

```powershell
python -m gmap_collector.main
```

使用项目内本地环境时：

```powershell
& '.\.conda\gmap\python.exe' -m gmap_collector.main
```

仅检查程序入口和基础依赖是否可用：

```powershell
python -m gmap_collector.main --check
```

## 使用方法

1. 打开软件后，先到“设置”页确认默认浏览器、自动化引擎、停留时间、滚动次数、连续失败暂停阈值和导出目录。
2. 在“任务配置”页选择国家和地区，地区被选择后默认包含该地区下的城市。
3. 在关键词输入框中输入行业关键词，一行一个。
4. 填写任务名称，生成任务预览，确认无误后创建任务。
5. 在“任务执行”页选择要运行的 Task，点击开始后软件会打开可视化浏览器窗口并顺序采集。
6. 运行过程中可以暂停、继续、停止，也可以对失败关键词进行重试。
7. Google Maps 采集完成后，可以进入“官网探索”页，选择来源 Task 并创建官网探索批次。
8. 官网探索会跳过没有官网的商家，并对有官网的商家提取电话、Email、社交媒体和 SEO Keywords。
9. 在“结果管理”页选择 Task 查看数据，并导出 CSV 或 Excel。

## 配置文件

主要配置文件位于 `config/` 目录。

| 文件 | 说明 |
| --- | --- |
| `config/locations.json` | 国家、地区、城市配置 |
| `config/app_config.json` | 浏览器、引擎、停留时间、滚动策略、失败策略、路径等运行配置 |

地区配置示例：

```json
{
  "countries": [
    {
      "name": "德国",
      "search_name": "Germany",
      "regions": [
        {
          "name": "Berlin",
          "search_name": "Berlin",
          "cities": [
            {
              "name": "Berlin",
              "search_name": "Berlin"
            }
          ]
        }
      ]
    }
  ]
}
```

通常情况下，基础运行参数建议直接在软件“设置”页中修改。

## 生成地区配置

如果需要根据自己的原始国家和城市数据重新生成 `config/locations.json`，可以使用内置脚本：

```powershell
python -m scripts.generate_locations_config --country-table tests\guojia\guojia2.html --cities tests\json-cities\cities.json --output config\locations.json
```

参数说明：

| 参数 | 说明 |
| --- | --- |
| `--country-table` | 国家数据 HTML 文件路径 |
| `--cities` | 城市 JSON 文件路径 |
| `--output` | 生成后的地区配置输出路径 |

脚本会尽量导入适合搜索的地点类型。如果某个国家缺少州或地区数据，会使用已有城市数据生成可用配置。

## 登录浏览器账号

如果需要先登录 Google 账号，可以使用脚本打开真实 Chrome，并把登录缓存保存到项目目录：

```powershell
python -m scripts.open_login_browser --browser chrome
```

默认缓存目录：

```text
drivers\selenium-cache\chrome
```

如果需要手动指定 Chrome 启动器路径：

```powershell
python -m scripts.open_login_browser --browser chrome --executable 'C:\Program Files\Google\Chrome\Application\chrome_proxy.exe'
```

如果当前电脑上 `chrome_proxy.exe` 表现异常，可以改用普通 Chrome：

```powershell
python -m scripts.open_login_browser --browser chrome --no-chrome-proxy
```

## 清理运行数据

清理数据库、日志、导出文件、调试输出和截图：

```powershell
python -m scripts.cleanup_runtime_data
```

同时清理浏览器登录缓存：

```powershell
python -m scripts.cleanup_runtime_data --include-browser-cache
```

也可以在软件“设置”页点击“清空数据库和缓存”。该操作会弹出确认提示，确认后会让项目回到接近全新运行状态，但不会删除源码和配置文件。

## 常用数据位置

| 路径 | 说明 |
| --- | --- |
| `data/app.sqlite3` | 本地 SQLite 数据库 |
| `exports/` | CSV 和 Excel 导出目录 |
| `logs/` | 运行日志目录 |
| `drivers/selenium-cache/` | Selenium 浏览器用户缓存 |
| `drivers/playwright-browsers/` | Playwright 浏览器缓存 |
| `config/locations.json` | 国家、地区、城市配置 |
| `config/app_config.json` | 软件运行配置 |

根目录下的 `keywords`、`keyword.txt`、调试输出、日志、数据库、浏览器缓存和导出文件属于本地运行数据，默认不应提交到 Git。

## 注意事项

- 当前采集过程使用单浏览器窗口顺序执行，适合稳定运行和人工观察。
- 软件只解析 Google Maps 搜索结果列表中已经加载出来的内容，不点击进入商家详情页。
- 软件不会自动绕过验证码、登录限制、访问限制或其他风控机制。
- 如果页面出现验证码、异常提示或疑似风控，应暂停任务并人工处理。
- Google Maps 页面结构和商家官网结构可能变化，字段解析结果会受页面实际内容影响。
- 官网探索优先使用静态 HTTP 请求，必要时会使用浏览器自动化作为兜底。

## 开源协议

本项目使用 `GPL-3.0-only` 协议开源，详情见 `LICENSE`。
