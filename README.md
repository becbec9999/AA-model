# 大类资产配置指标监控面板

## 项目简介

AA-Model 是一个**量化大类资产配置指标研究框架**，核心设计理念是**数据与计算解耦**，指标单文件存储，便于多人协同与多因子回测。

---

## 快速开始（新手必读）

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

---

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

**简单理解**：
1. `AA_Indicators.py` 计算指标 → 保存到 `指标结果库/`
2. `server.py` 读取数据 → 提供 API 给前端
3. 前端页面 → 展示图表，支持时间范围切换

---

## 目录结构

```
AA-Model/
├── AA_Indicators.py       # 核心：指标计算引擎
├── server.py              # 核心：Web 服务入口
├── config/                # 配置目录
│   ├── tickers.py        # 标的配置（代码、名称、颜色）
│   ├── indicators.py      # 指标模式定义
│   └── paths.py          # 路径配置
├── api/                   # API 层
│   ├── routes.py         # API 路由
│   └── service.py        # 数据服务
├── data/                  # 数据模块
│   ├── loader.py         # 数据加载器
│   └── discover.py       # 指标自动发现
├── charts/                # 图表工厂
├── static/                # 前端静态文件
│   ├── css/style.css
│   └── js/app.js
├── templates/             # HTML 模板
│   └── index.html
└── 指标结果库/            # 预计算的指标数据（.pkl）
```

---

## 新手指南：如何添加指标

### 方式一：添加新标的（已有指标类型）

如果只是添加一个新的指数/股票标的，只需编辑 `config/tickers.py`：

```python
TICKER_CONFIG = {
    '000300.SH': {'name': '沪深300', 'color': '#00b8a9'},
    '000905.SH': {'name': '中证500', 'color': '#f75b5b'},
    '000852.SH': {'name': '中证1000', 'color': '#f7cc35'},
    # 添加新标的...
}
```

然后运行：
```bash
python AA_Indicators.py
```

系统会自动为新标的计算所有已有类型的指标。

### 方式二：添加全新指标类型

如果要添加全新的指标计算方法，需要修改 `AA_Indicators.py`：

```python
# 1. 在 VolumePriceIndicators 类中添加计算方法
def calc_and_save_new_indicator(self, ticker: str, n: int = 20):
    """新指标说明"""
    df = self.fetch(ticker)
    # 你的计算逻辑
    result = df['close'].rolling(window=n).mean()  # 示例
    result = result.dropna()

    # 保存到指标结果库
    filepath = os.path.join(OUTPUT_DIR, f'{ticker}_new_indicator_{n}d.pkl')
    result.to_pickle(filepath)
    return filepath

# 2. 在 run() 方法中调用
def run(self):
    for ticker in self.tickers:
        self.calc_and_save_new_indicator(ticker, n=20)
```

### 方式三：添加指标分类

如果要为指标分配到不同的分类显示，编辑 `static/js/app.js` 中的 `INDICATOR_CATEGORIES`：

```javascript
const INDICATOR_CATEGORIES = {
    '量价指标类': {
        subcategories: {
            '趋势跟踪': { patterns: ['ma', 'ma_dev'], description: '均线及偏离度' },
            '动量反转': { patterns: ['mom', 'rsi'], description: '动量指标及RSI' },
            '波动风险': { patterns: ['vol'], description: '年化波动率' },
            '市场情绪': { patterns: ['amt', 'pchg_abs'], description: '成交额及换手率' },
            '风格切换': { patterns: ['rs', 'rt'], description: '相对强弱比' },
            // 添加新分类...
        }
    },
    // ...
};
```

---

## 使用说明

### 页面布局
- **左侧**：指标导航（按分类折叠）
- **顶部**：时间范围选择按钮
- **右侧**：图表展示区域

### 时间范围
| 按钮 | 含义 |
|------|------|
| 1M | 最近1个月 |
| 3M | 最近3个月 |
| 6M | 最近6个月 |
| YTD | 今年至今 |
| 1Y | 最近1年 |
| 2Y | 最近2年 |
| 3Y | 最近3年 |
| 5Y | 最近5年 |
| All | 全部历史 |

**注意**：时间范围基于**数据的最晚日期**计算，而非系统当前日期。

### 自定义日期
使用日期输入框选择开始和结束日期，点击"应用"按钮。

---

## 数据更新

当原始数据更新后，运行以下命令重新计算所有指标：

```bash
python AA_Indicators.py
```

计算完成后，刷新浏览器页面即可看到最新数据。

---

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 主页面 |
| `/api/indicators` | GET | 获取所有指标列表 |
| `/api/charts/{chart_id}` | GET | 获取指定图表数据 |
| `/api/tickers` | GET | 获取所有标的 |
| `/health` | GET | 健康检查 |

---

## 常见问题

**Q: 服务启动失败？**
A: 检查依赖是否安装：`pip install pandas numpy plotly fastapi uvicorn`

**Q: 图表不显示？**
A: 检查 `指标结果库/` 目录下是否有 .pkl 数据文件

**Q: 1M/3M 等时间范围显示全历史？**
A: 数据最新日期可能早于当前日期减1个月，需要更新原始数据

**Q: 如何部署到服务器？**
A: `uvicorn server:app --host 0.0.0.0 --port 8000`

---

## 技术栈

- **后端**：FastAPI + Python
- **前端**：原生 JavaScript + Plotly.js
- **数据**：Pandas + Pickle

---

## 联系方式

项目地址：https://github.com/becbec9999/AA-model
