"""标的配置"""
import re

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
    'IF': {'name': 'IF股指期货', 'color': '#2196f3'},
    'IH': {'name': 'IH股指期货', 'color': '#ffb300'},
    'IC': {'name': 'IC股指期货', 'color': '#ff5722'},
    'IM': {'name': 'IM股指期货', 'color': '#7e57c2'},
}

# 用于兼容旧代码的别名
TICKER_COLORS = {k: v['color'] for k, v in TICKER_CONFIG.items()}
TICKER_NAMES = {k: v['name'] for k, v in TICKER_CONFIG.items()}


def get_ticker_color(ticker: str) -> str:
    """获取标的颜色"""
    color = TICKER_CONFIG.get(ticker, {}).get('color')
    if color:
        return color

    # 股指期货合约：IF/IH/IC/IM + 两位月份 + .CFE
    m = re.match(r'^(IF|IH|IC|IM)\d{2}\.CFE$', ticker)
    if m:
        return TICKER_CONFIG.get(m.group(1), {}).get('color', '#888888')

    return '#888888'


def get_ticker_name(ticker: str) -> str:
    """获取标的名称"""
    name = TICKER_CONFIG.get(ticker, {}).get('name')
    if name:
        return name

    m = re.match(r'^(IF|IH|IC|IM)(\d{2})\.CFE$', ticker)
    if m:
        month_map = {
            "00": "当月",
            "01": "近月",
            "02": "下季",
            "03": "隔季",
        }
        suffix = m.group(2)
        label = month_map.get(suffix, suffix)
        return f"{m.group(1)}{label}合约"

    return ticker
