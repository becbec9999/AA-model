# AA-Model 项目文档

## 项目概述

**AA-Model** 是一个量化大类资产配置指标研究框架，核心设计理念是**数据与计算解耦**，指标单文件存储，便于多人协同与多因子回测。

---

## 1. 项目整体架构和目录结构

```
e:/code_source/AA-model/
├── AA_Indicators.py              # 核心指标计算引擎（数据引擎 + 量价类指标集）
├── 大类资产配置指标展示.py         # 可视化展示脚本（生成交互式 HTML 报告）
├── 每日量价跟踪报告.html          # Plotly 生成的交互式图表报告（V4.0专业金融终端风格）
└── 指标结果库/                    # 输出的指标文件存储目录（PKL格式）
    ├── {ticker}_{indicator}.pkl      # 按标的和指标类型命名的 PKL 文件
    └── ...
```

### 数据源目录（需在 DataLoader 中配置）
- **WIN**: `E:\数据库\ETF跟踪指数量价数据-日度更新\ETF跟踪指数量价数据-日度更新`

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
| 量价 | `E:\数据库\ETF跟踪指数量价数据-日度更新\ETF跟踪指数量价数据-日度更新` |
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

### 2.3 大类资产配置指标展示（V4.0）
位置：`大类资产配置指标展示.py`

**职责**：使用 Plotly 生成交互式 HTML 图表

**UI设计**：参考 TradingView/Bloomberg 专业金融终端风格
- 深蓝黑背景（#131722）
- 高对比度彩色线条
- 固定顶部工具栏（含时间范围选择器）
- 左侧边栏含标的复选框和指标导航
- 图表容器固定 400px 高度
- 右侧 Y 轴标签

**主要功能**：
- 指标按标的拆分显示（每个标的独立图表）
- 相对强弱指标每个对比对独立图表
- 时间范围快速切换（1M / 3M / 6M / YTD / 1Y / ALL）
- Plotly 原生交互（缩放、拖拽、十字线）

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
| 8841431.WI | 万得全A |
| 881001.WI | 申万A股 |

---

## 4. 依赖的关键库

```
pandas        # 数据处理
numpy         # 数值计算
plotly        # 交互式图表（仅展示模块）
```

**安装方式**：
```bash
pip install pandas numpy plotly
```

---

## 5. 常用运行命令

### 5.1 运行指标计算
```bash
python AA_Indicators.py
```

### 5.2 生成可视化报告
```bash
python 大类资产配置指标展示.py
```

### 5.3 查看报告
在浏览器中打开 `每日量价跟踪报告.html`

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

## 8. 版本历史

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
