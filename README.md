# 大类资产配置指标监控面板

## 项目简介

AA-Model 是一个量化大类资产配置指标研究框架，核心设计理念是**数据与计算解耦**，指标单文件存储，便于多人协同与多因子回测。

## 快速开始

### 1. 安装依赖

```bash
pip install pandas numpy plotly fastapi uvicorn
```

### 2. 启动服务

```bash
cd e:\AA-model
python server.py
```

### 3. 访问页面

浏览器打开：**http://localhost:8000**

## 项目架构

```
AA-Model/
├── AA_Indicators.py       # 量化指标计算框架（预计算指标到 指标结果库/）
├── server.py              # FastAPI 服务入口
├── api/                   # API 层
│   ├── models.py         # 数据模型
│   ├── routes.py         # API 路由
│   └── service.py        # 数据服务
├── static/               # 前端静态文件
│   ├── css/style.css
│   └── js/app.js
├── templates/             # HTML 模板
│   └── index.html
├── config/               # 配置模块
│   ├── tickers.py       # 标的配置
│   ├── indicators.py    # 指标模式
│   └── paths.py         # 路径配置
├── data/                 # 数据模块
│   ├── loader.py        # 数据加载
│   └── discover.py      # 指标发现
├── charts/              # 图表工厂
│   └── factory.py
├── 指标结果库/           # 预计算指标数据（.pkl/.csv）
└── 大类资产配置指标展示.py  # 旧版 HTML 单文件（已废弃）
```

## 工作流程

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ AA_Indicators.py│ ──> │   指标结果库/    │ <─> │  server.py API  │
│  (指标计算)      │     │   (.pkl文件)    │     │  (数据服务)     │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                           │
                                                           v
                                                  ┌─────────────────┐
                                                  │   浏览器前端     │
                                                  │  (Plotly图表)   │
                                                  └─────────────────┘
```

## 配置说明

### 添加新标的

编辑 `config/tickers.py`：

```python
TICKER_CONFIG = {
    '000300.SH': {'name': '沪深300', 'color': '#00b8a9'},
    '000905.SH': {'name': '中证500', 'color': '#f75b5b'},
    # 添加新标的...
}
```

### 添加新指标模式

编辑 `config/indicators.py`：

```python
INDICATOR_PATTERNS = {
    'new_indicator': {
        'category': '量价类',
        'type': '趋势',
        'name': '新指标',
        'window': True,  # 是否有窗口参数
    },
    # ...
}
```

### 修改数据路径

编辑 `config/paths.py`：

```python
OUTPUT_DIR = r"e:\AA-model\指标结果库"
DATA_DIR = r"E:\数据库\ETF跟踪指数量价数据-日度更新\ETF跟踪指数量价数据-日度更新"
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 主页面 |
| `/api/indicators` | GET | 获取所有指标列表 |
| `/api/charts/{chart_id}` | GET | 获取指定图表数据 |
| `/api/tickers` | GET | 获取所有标的 |
| `/health` | GET | 健康检查 |

## 使用说明

1. **查看指标**：点击左侧导航栏中的指标
2. **切换时间范围**：点击顶部时间按钮（1M/3M/6M/YTD/1Y/ALL）
3. **自定义区间**：选择开始和结束日期，点击"应用"
4. **刷新数据**：点击右上角刷新按钮或重新运行 `AA_Indicators.py`

## 数据更新流程

1. 修改 `AA_Indicators.py` 中的标的列表（如果需要）
2. 运行 `python AA_Indicators.py` 重新计算指标
3. 刷新浏览器页面查看最新数据

## 技术栈

- **后端**：FastAPI + Python
- **前端**：原生 JavaScript + Plotly.js
- **数据**：Pandas + Pickle

## 常见问题

**Q: 服务启动失败？**
A: 检查是否安装了所有依赖：`pip install fastapi uvicorn`

**Q: 图表不显示？**
A: 检查 `指标结果库/` 目录下是否有数据文件

**Q: 如何添加新的指标？**
A: 在 `AA_Indicators.py` 中添加计算方法，然后在 `config/indicators.py` 中注册
