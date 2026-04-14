"""标的配置"""

# 标的配置：代码 -> {name: 中文名, color: 颜色}
TICKER_CONFIG = {
    '000300.SH': {'name': '沪深300', 'color': '#00b8a9'},
    '000905.SH': {'name': '中证500', 'color': '#f75b5b'},
    '000852.SH': {'name': '中证1000', 'color': '#f7cc35'},
    '932000.CSI': {'name': '科创50', 'color': '#4caf50'},
    '8841431.WI': {'name': '万得微盘股指数', 'color': '#9c27b0'},
    '881001.WI': {'name': '万得全A', 'color': '#2196f3'},
    'SH_510050IV.WI': {'name': '50ETF隐含波动率', 'color': '#ff9800'},
    'SH_510300IV.WI': {'name': '300ETF隐含波动率', 'color': '#ffb74d'},
    'SH_510500IV.WI': {'name': '500ETF隐含波动率', 'color': '#ff7043'},
    'CFE_000852IV.WI': {'name': '中证1000股指隐含波动率', 'color': '#ab47bc'},
}

# 用于兼容旧代码的别名
TICKER_COLORS = {k: v['color'] for k, v in TICKER_CONFIG.items()}
TICKER_NAMES = {k: v['name'] for k, v in TICKER_CONFIG.items()}


def get_ticker_color(ticker: str) -> str:
    """获取标的颜色"""
    return TICKER_CONFIG.get(ticker, {}).get('color', '#888888')


def get_ticker_name(ticker: str) -> str:
    """获取标的名称"""
    return TICKER_CONFIG.get(ticker, {}).get('name', ticker)
