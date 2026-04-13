# AA-Model 项目文档

## 项目概述

**AA-Model** 是一个量化大类资产配置指标研究框架，核心设计理念是**数据与计算解耦**，指标单文件存储，便于多人协同与多因子回测。

---

## 1. 项目整体架构和目录结构

```
e:/AA-model/
├── AA_Indicators.py              # 核心指标计算引擎（数据引擎 + 量价类指标集）
├── server.py                     # FastAPI 服务入口（V5.0）
├── README.md                     # 操作文档
├── CLAUDE.md                     # 项目文档
├── .gitignore                    # Git忽略文件配置
│
├── api/                          # API 层
│   ├── __init__.py
│   ├── models.py                 # Pydantic 数据模型
│   ├── routes.py                 # API 路由定义
│   └── service.py                # 数据服务（读取指标库）
│
├── config/                       # 配置模块
│   ├── __init__.py
│   ├── tickers.py               # 标的配置（代码、名称、颜色）
│   ├── indicators.py            # 指标模式定义
│   └── paths.py                 # 路径配置
│
├── data/                        # 数据模块
│   ├── __init__.py
│   ├── loader.py                # 数据加载器
│   └── discover.py              # 指标自动发现
│
├── charts/                      # 图表工厂
│   └── factory.py
│
├── static/                      # 前端静态文件
│   ├── css/style.css
│   └── js/app.js
│
├── templates/                   # HTML 模板
│   └── index.html
│
├── 指标结果库/                   # 输出的指标文件存储目录（PKL格式）
│   ├── {ticker}_{indicator}.pkl
│   └── ...
│
└── 原始数据/                     # 原始数据备份
```

### 数据源目录（需在 DataLoader 中配置）
- **WIN**: `E:\择时模型数据\指数量价数据-非日度更新`

---

## 2. 核心模块及功能

### 2.1 DataLoader（数据引擎）
位置：`AA_Indicators.py` 第 17-76 行

**职责**：底层数据的抓取、清洗与标准化

**核心方法**：
- `fetch(ticker, category="量价")` → 返回标准化 DataFrame（日期为索引，列名小写）

**数据路由表（source_map）**：
| category | WIN 路径 |
|----------|----------|
| 量价 | `E:\择时模型数据\指数量价数据-非日度更新` |
| 宏观 | `原始数据\宏观经济数据` |
| 估值 | `原始数据\指数估值数据` |

### 2.2 VolumePriceIndicators（量价类指标库）
位置：`AA_Indicators.py` 第 80-242 行

**职责**：调用数据引擎计算各类技术指标

**输出格式**：统一输出为 PKL 格式（更轻量，Python原生支持）

**指标分类**：

| 方法名 | 功能 | 输出文件 |
|--------|------|----------|
| `calc_and_save_amt` | 成交额 | `{ticker}_amt.pkl` |
| `calc_and_save_amt_ratio` | 成交额占全市场比重 | `{ticker}_vs_market_amt_ratio.pkl` |
| `calc_relative_strength` | 相对强弱比 | `{ticker_a}_vs_{ticker_b}_rs.pkl` |
| `calc_relative_turnover` | 相对换手率 | `{ticker_a}_vs_{ticker_b}_rt.pkl` |
| `calc_and_save_pchg_abs` | N日涨跌幅绝对值 | `{ticker}_pchg_abs_{n}d.pkl` |
| `calc_and_save_mom` | 动量指标 | `{ticker}_mom_{n}d.pkl` |
| `calc_and_save_ma` | 移动均线 | `{ticker}_ma_{n}d.pkl` |
| `calc_and_save_ma_turnover` | 移动平均换手率 | `{ticker}_ma_turnover_{n}d.pkl` |
| `calc_and_save_ma_deviation` | 均线偏离度 | `{ticker}_ma_dev_{n}d.pkl` |
| `calc_and_save_rsi_percentile` | RSI 及分位值 | `{ticker}_rsi_analysis.pkl` |
| `calc_and_save_volatility` | 年化波动率 | `{ticker}_vol_{n}d.pkl` |

### 2.3 FastAPI 服务（V5.0）
位置：`server.py` + `api/` 目录

**职责**：提供 REST API，按需加载图表数据

**API 端点**：
| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 返回主页面 |
| `/api/indicators` | GET | 获取所有指标列表（元数据） |
| `/api/charts/{chart_id}` | GET | 获取指定图表数据（JSON） |
| `/api/tickers` | GET | 获取所有标的列表 |
| `/health` | GET | 健康检查 |

---

## 3. 数据来源、格式与表结构

### 3.1 原始数据格式
- **来源**：同花顺 ETF 跟踪指数日度数据
- **格式**：CSV 文件
- **列名**：小写处理后为 `time`, `open`, `high`, `low`, `close`, `volume`, `amt`（成交额）, `turnover`, `free_turn` 等

### 3.2 输出指标文件格式
- **格式**：PKL（pickle）
- **索引列**：`time`（日期，格式 YYYY-MM-DD）
- **值列**：指标名称

### 3.3 主要标的代码
| 代码 | 名称 |
|------|------|
| 000300.SH | 沪深300 |
| 000905.SH | 中证500 |
| 000852.SH | 中证1000 |
| 932000.CSI | 科创50 |
| 8841431.WI | 万得微盘股指数 |
| 881001.WI | 万得全A |

---

## 4. 依赖的关键库

```
pandas        # 数据处理
numpy         # 数值计算
plotly        # 交互式图表
fastapi       # Web 框架
uvicorn       # ASGI 服务器
```

**安装方式**：
```bash
pip install pandas numpy plotly fastapi uvicorn
```

---

## 5. 常用运行命令

### 5.1 启动可视化服务（推荐）
```bash
python server.py
# 浏览器访问 http://localhost:8000
```

### 5.2 运行指标计算
```bash
python AA_Indicators.py
```

### 5.3 旧版 HTML 单文件（已废弃）
```bash
python 大类资产配置指标展示.py
# 浏览器打开 每日量价跟踪报告.html
```

---

## 6. 项目约定和规范

### 6.1 文件命名规范
- 输出指标文件：`{标的代码}_{指标类型}.pkl`
- 例如：`000300.SH_ma_20d.pkl`，`000300.SH_vs_000905.SH_rs.pkl`

### 6.2 数据规范
- 列名统一小写：`date`/`time`, `open`, `high`, `low`, `close`, `volume`, `amt`, `turnover`, `free_turn`
- 日期索引格式：`YYYY-MM-DD`
- 空值处理：自动 dropna

### 6.3 计算规范
- **波动率**：对数收益率 × √242 × 100（A股年交易日约242天）
- **均线偏离度**：(CLOSE - MA) / MA × 100
- **RSI 参数**：默认 14 日 RSI，120 日分位窗口

### 6.4 数据与计算解耦设计
- DataLoader 负责数据读取和清洗
- VolumePriceIndicators 负责指标计算和落盘
- FastAPI 服务负责按需加载和展示
- 研究员只需调用 `calc_and_save_*` 方法即可，无需关心 IO

---

## 7. 关键公式

| 指标 | 公式 |
|------|------|
| 涨跌幅绝对值 | ABS((CLOSE / CLOSE(N) - 1) × 100) |
| 动量 | (CLOSE / CLOSE(N) - 1) × 100 |
| 移动均线 | MA(CLOSE, N) |
| 均线偏离度 | (CLOSE - MA) / MA × 100 |
| 年化波动率 | Std(Log_Return, N) × √242 × 100 |
| RSI | 100 - (100 / (1 + Avg_Gain / Avg_Loss)) |

---

## 8. 时间范围功能说明

### 8.1 时间范围计算逻辑
前端时间范围（1M/3M/6M/YTD/1Y/ALL）基于**图表数据的最新日期**计算，而非系统当前日期。

**相关函数**（`static/js/app.js`）：
- `getDateRange(range, dataEndDate)` - 根据数据最新日期计算时间范围起点
- `applyTimeRange(rangeOrStart, endDate)` - 应用时间范围到 Plotly 图表

**计算规则**：
| 范围 | 计算方式 |
|------|----------|
| 1M | dataEndDate - 1个月 |
| 3M | dataEndDate - 3个月 |
| 6M | dataEndDate - 6个月 |
| YTD | 当年1月1日 |
| 1Y | dataEndDate - 1年 |
| 2Y | dataEndDate - 2年 |
| 3Y | dataEndDate - 3年 |
| 5Y | dataEndDate - 5年 |
| ALL | 显示全历史 |

**示例**（数据最新日期为 2026-02-05）：
- 1M: 2026-01-05 → 2026-02-05 (24点)
- 3M: 2025-11-05 → 2026-02-05 (65点)
- 6M: 2025-08-05 → 2026-02-05 (125点)

### 8.2 缓存刷新
JS 文件带有版本参数 `?v=20260322`，更新代码后刷新页面即可加载新版本。

---

## 9. 代码审查问题（已修复）

### S1 - 严重问题（已全部修复）

| 文件 | 行号 | 问题 | 修复状态 |
|------|------|------|----------|
| `AA_Indicators.py` | 26-38 | `source_map` 重复定义，MAC配置永不生效 | ✅ 已修复：使用 `platform.system()` 自动检测 |
| `AA_Indicators.py` | 206-208 | RSI计算存在除零风险 | ✅ 已修复：返回 NaN（无波动时更合理） |
| `AA_Indicators.py` | 97 | `inplace=True` 已废弃 | ✅ 已修复：改为 `df = df.dropna()` |

### S2 - 高风险问题（已全部修复）

| 文件 | 行号 | 问题 | 修复状态 |
|------|------|------|----------|
| `server.py` | 31-37 | CORS配置 `allow_origins=["*"]` 不安全 | ✅ 已修复：使用环境变量 `ALLOWED_ORIGINS` |
| `server.py` | 73-76 | `reload=True` 影响生产性能 | ✅ 已修复：通过环境变量 `RELOAD` 控制 |
| `config/paths.py` | 4-10 | 路径硬编码无法跨平台 | ✅ 已修复：支持环境变量 + 相对路径 |
| `AA_Indicators.py` | 130-131 | 相对强弱计算无除零保护 | ✅ 已修复：使用 `np.where` 处理 |
| `AA_Indicators.py` | 238 | 硬编码242交易日数量 | ✅ 已修复：定义为常量 `TRADING_DAYS_PER_YEAR` |

### S3 - 中等风险问题（已全部修复）

| 文件 | 行号 | 问题 | 修复状态 |
|------|------|------|----------|
| `api/service.py` | 153-157 | `to_json()` 被调用两次，效率低 | ✅ 已修复：一次调用并存入变量 |
| `api/service.py` 与 `charts/factory.py` | - | `_hex_to_rgba` 函数重复实现 | ⚠️ 保留：factory.py 未被使用 |
| `data/discover.py` | 72 | 可使用 `glob.glob()` 更高效 | ✅ 已修复：使用 glob.glob 匹配 |
| `api/service.py` | 103-158 | 无缓存机制，大数据量时性能差 | ✅ 已修复：添加 `_chart_cache` 缓存 |

---

## 10. 版本历史

### V5.4 (2026-04-13)
- **图表渲染修复**：修复前端 plotly.js 无法正确解码压缩数组格式的问题
- **api/service.py**：改用 `to_plotly_json()` + `PlotlyJSONEncoder` 替代 `to_json()`
- **数据序列化优化**：将 x/y 数据强制转为 list，避免 numpy dtype/bdata 压缩格式
- **旧版同步**：`大类资产配置指标展示.py` 同步相同修复

### V5.3 (2026-03-23)
- **代码审查修复**：修复全部 12 个 S1-S3 级问题
- **source_map 修复**：使用 `platform.system()` 自动检测操作系统
- **除零保护**：RSI 和相对强弱添加 NaN 处理
- **inplace=True 移除**：改用链式调用
- **CORS 优化**：使用环境变量 `ALLOWED_ORIGINS` 控制
- **reload 优化**：使用环境变量 `RELOAD` 控制
- **路径配置优化**：支持环境变量覆盖
- **常量提取**：242 交易日定义为 `TRADING_DAYS_PER_YEAR`
- **性能优化**：to_json 单次调用、glob.glob 替代 listdir
- **缓存机制**：ChartService 添加 `_chart_cache`

### V5.2 (2026-03-22)
- **时间范围修复**：1M/3M/6M/YTD/1Y 基于图表数据最新日期计算，而非系统当前日期
- **新增时间范围选项**：增加 2Y、3Y、5Y 三个选项
- **getDateRange 函数重构**：新增 `dataEndDate` 参数，支持自定义基准日期
- **applyTimeRange 优化**：使用数据的实际日期范围计算可见点
- **Y轴自适应保持**：点时间区间时 `yaxis.autorange: true`，Y轴保持自适应缩放
- **JS缓存刷新**：添加版本参数避免浏览器缓存旧代码

### V5.1 (2026-03-21)
- **架构升级**：从 HTML 单文件改为 FastAPI 本地服务
- **按需加载**：图表数据通过 API 独立加载，解决大数据量导致浏览器卡顿问题
- **模块化重构**：前后端分离，代码更易维护
- **保留旧版**：保留 `大类资产配置指标展示.py` 作为备选

### V4.0 (2026-03-20)
- 完全重写可视化界面，采用专业金融终端风格
- 图表按标的拆分独立显示，避免拥挤
- 相对强弱指标每个对比对独立图表
- 实现时间范围快速切换功能
- 修复柱状图在深色背景下的可见性问题
- 高对比度配色方案

### V3.0
- 引入动态指标发现机制
- 支持 PKL 输出格式

### 早期版本
- 基础指标计算框架搭建
- CSV 输出格式
