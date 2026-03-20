"""配置模块"""
from .tickers import TICKER_CONFIG, get_ticker_color, get_ticker_name
from .indicators import INDICATOR_PATTERNS
from .paths import OUTPUT_DIR, DATA_DIR, OUTPUT_FILE

__all__ = [
    'TICKER_CONFIG',
    'get_ticker_color',
    'get_ticker_name',
    'INDICATOR_PATTERNS',
    'OUTPUT_DIR',
    'DATA_DIR',
    'OUTPUT_FILE',
]
