"""指标模式定义"""

INDICATOR_PATTERNS = {
    'ma': {'category': '量价类', 'type': '趋势', 'name': '均线', 'window': True},
    'ma_dev': {'category': '量价类', 'type': '趋势', 'name': '均线偏离度', 'window': True},
    'high_new': {'category': '量价类', 'type': '趋势', 'name': '是否新高', 'window': True},
    'low_new': {'category': '量价类', 'type': '趋势', 'name': '是否新低', 'window': True},
    'mom': {'category': '量价类', 'type': '动量', 'name': '动量', 'window': True},
    'return_acf1': {'category': '量价类', 'type': '动量', 'name': '趋势连续度', 'window': True},
    'erp': {'category': '量价类', 'type': '动量', 'name': '股债风险溢价', 'window': True},
    'iv': {'category': '量价类', 'type': '动量', 'name': '隐含波动率', 'window': False},
    'vol': {'category': '量价类', 'type': '动量', 'name': '波动率', 'window': True},
    'amt': {'category': '量价类', 'type': '情绪', 'name': '成交额', 'window': False},
    'pchg_abs': {'category': '量价类', 'type': '情绪', 'name': '涨跌幅绝对值', 'window': False},
    'rs': {'category': '量价类', 'type': '情绪', 'name': '相对强弱', 'window': False},
    'rt': {'category': '量价类', 'type': '情绪', 'name': '相对换手率', 'window': False},
    'rsi': {'category': '量价类', 'type': '动量', 'name': 'RSI', 'window': True},
}
