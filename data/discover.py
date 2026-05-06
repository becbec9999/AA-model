"""指标自动发现"""
import os
import re
import glob
from typing import Optional

from config import INDICATOR_PATTERNS


def classify_indicator(filename: str) -> Optional[dict]:
    """从文件名解析指标信息

    Args:
        filename: 文件名（不含路径）

    Returns:
        解析结果字典，或 None 如果无法解析
    """
    name = filename.replace('.csv', '').replace('.pkl', '')

    # 跨标的对比格式: tickerA_vs_tickerB_pattern
    cross_pattern = r'(.+?)_vs_(.+?)_(.+)'
    cross_match = re.match(cross_pattern, name)
    if cross_match:
        ticker_a, ticker_b, pattern = cross_match.groups()
        return {
            'pattern': pattern,
            'ticker_a': ticker_a,
            'ticker_b': ticker_b,
            'ticker': f'{ticker_a}_vs_{ticker_b}',
            'window': None,
            'is_cross': True
        }

    # 单标的格式: ticker_pattern(window)?
    # 注意 ticker 可能包含下划线（如 SH_510300IV.WI），因此使用“从右向左”匹配 pattern/window
    known_patterns = sorted(INDICATOR_PATTERNS.keys(), key=len, reverse=True)
    for pattern in known_patterns:
        suffix = f"_{pattern}"
        if not name.endswith(suffix) and f"_{pattern}_" not in name:
            continue

        # 先尝试带窗口：..._{pattern}_{N}d
        window_match = re.match(rf"^(.+)_{re.escape(pattern)}_(\d+)d$", name)
        if window_match:
            ticker, window = window_match.groups()
            return {
                'pattern': pattern,
                'ticker': ticker,
                'ticker_a': None,
                'ticker_b': None,
                'window': int(window),
                'is_cross': False
            }

        # 再尝试不带窗口：..._{pattern}
        plain_match = re.match(rf"^(.+)_{re.escape(pattern)}$", name)
        if plain_match:
            ticker = plain_match.group(1)
            return {
                'pattern': pattern,
                'ticker': ticker,
                'ticker_a': None,
                'ticker_b': None,
                'window': None,
                'is_cross': False
            }

    return None


def discover_indicators(output_dir: str) -> dict:
    """扫描目录发现所有有效指标

    Args:
        output_dir: 指标文件目录

    Returns:
        按 category -> type 分组的指标列表
        {
            '量价类': {
                '趋势': [...],
                '动量': [...],
                '情绪': [...]
            }
        }
    """
    if not os.path.exists(output_dir):
        print(f"[ERROR] Directory not found: {output_dir}")
        return {}

    result = {}
    # 使用 glob.glob 更高效地匹配文件
    indicator_files = [
        os.path.basename(f) for f in glob.glob(os.path.join(output_dir, '*.pkl'))
    ] + [
        os.path.basename(f) for f in glob.glob(os.path.join(output_dir, '*.csv'))
    ]

    print(f"[INFO] Found {len(indicator_files)} indicator files")

    for filename in indicator_files:
        info = classify_indicator(filename)
        if not info:
            continue

        pattern = info['pattern']
        if pattern not in INDICATOR_PATTERNS:
            continue

        config = INDICATOR_PATTERNS[pattern]
        category = config['category']
        indicator_type = config['type']

        if category not in result:
            result[category] = {}

        indicator_info = {
            'filename': filename,
            'filepath': os.path.join(output_dir, filename),
            'pattern': pattern,
            'name': config['name'],
            'ticker': info['ticker'],
            'ticker_a': info.get('ticker_a'),
            'ticker_b': info.get('ticker_b'),
            'window': info['window'],
            'is_cross': info.get('is_cross', False),
        }

        if indicator_type not in result[category]:
            result[category][indicator_type] = []
        result[category][indicator_type].append(indicator_info)

    return result
