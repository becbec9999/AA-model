#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大类资产配置指标展示程序 V4.0
=====================================
专业金融终端风格设计
参考: TradingView, Bloomberg, Ant Design
"""

import os
import re
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ==========================================
# 配置区
# ==========================================

OUTPUT_DIR = r"e:\code_source\AA-model\指标结果库"
DATA_DIR = r"E:\数据库\ETF跟踪指数量价数据-日度更新\ETF跟踪指数量价数据-日度更新"
OUTPUT_FILE = "每日量价跟踪报告.html"

# 高对比度配色方案
TICKER_COLORS = {
    '000300.SH': '#00b8a9',  # 青色 - 沪深300
    '000905.SH': '#f75b5b',   # 红色 - 中证500
    '000852.SH': '#f7cc35',   # 黄色 - 中证1000
    '932000.CSI': '#4caf50',  # 绿色 - 科创50
    '8841431.WI': '#9c27b0', # 紫色
    '881001.WI': '#2196f3',   # 蓝色
}

TICKER_NAMES = {
    '000300.SH': '沪深300',
    '000905.SH': '中证500',
    '000852.SH': '中证1000',
    '932000.CSI': '科创50',
    '8841431.WI': '微利全A',
    '881001.WI': '万得全A',
}

INDICATOR_PATTERNS = {
    'ma': {'category': '量价类', 'type': '趋势', 'name': '均线', 'window': True},
    'ma_dev': {'category': '量价类', 'type': '趋势', 'name': '均线偏离度', 'window': True},
    'mom': {'category': '量价类', 'type': '动量', 'name': '动量', 'window': True},
    'vol': {'category': '量价类', 'type': '动量', 'name': '波动率', 'window': True},
    'amt': {'category': '量价类', 'type': '情绪', 'name': '成交额', 'window': False},
    'pchg_abs': {'category': '量价类', 'type': '情绪', 'name': '涨跌幅绝对值', 'window': False},
    'rs': {'category': '量价类', 'type': '情绪', 'name': '相对强弱', 'window': False},
    'rt': {'category': '量价类', 'type': '情绪', 'name': '相对换手率', 'window': False},
    'rsi': {'category': '量价类', 'type': '动量', 'name': 'RSI', 'window': True},
}


# ==========================================
# 核心函数
# ==========================================

def classify_indicator(filename: str) -> dict:
    name = filename.replace('.csv', '').replace('.pkl', '')

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

    single_pattern = r'(.+?)_(.+?)(?:_(\d+)d)?$'
    single_match = re.match(single_pattern, name)
    if single_match:
        ticker, pattern, window = single_match.groups()
        return {
            'pattern': pattern,
            'ticker': ticker,
            'ticker_a': None,
            'ticker_b': None,
            'window': int(window) if window else None,
            'is_cross': False
        }

    return None


def discover_available_indicators(output_dir: str) -> dict:
    if not os.path.exists(output_dir):
        print(f"[ERROR] Directory not found: {output_dir}")
        return {}

    result = {}
    indicator_files = [f for f in os.listdir(output_dir) if f.endswith(('.pkl', '.csv'))]

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
            result[category] = {'趋势': [], '动量': [], '情绪': []}

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

        if indicator_type in result[category]:
            result[category][indicator_type].append(indicator_info)

    return result


def load_indicator(filepath: str) -> pd.DataFrame:
    try:
        if filepath.endswith('.pkl'):
            df = pd.read_pickle(filepath)
        else:
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        df.index.name = 'date'
        return df
    except Exception as e:
        print(f"[ERROR] Failed to load {filepath}: {e}")
        return None


# ==========================================
# 图表创建函数
# ==========================================

def create_line_chart(title: str, traces_data: list, subplot_titles: list = None) -> go.Figure:
    """创建标准线图 - 专业风格"""
    rows = len(traces_data) if len(traces_data) > 1 else 1

    fig = make_subplots(
        rows=rows, cols=1,
        subplot_titles=subplot_titles or [title],
        vertical_spacing=0.08,
        shared_xaxes=True,
        row_heights=[1.0] * rows if rows > 1 else None
    )

    for idx, (trace_name, trace_y, color, width) in enumerate(traces_data, 1):
        fig.add_trace(
            go.Scatter(
                x=trace_y.index,
                y=trace_y.values,
                mode='lines',
                name=trace_name,
                line=dict(
                    color=color,
                    width=width or 2,
                    shape='spline',  # 平滑曲线
                ),
                fill='tozeroy' if idx == 1 else None,
                fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)' if idx == 1 else None,
            ),
            row=idx, col=1
        )

    # 更新布局 - 专业深色主题
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            x=0.5,
            xanchor='center',
            font=dict(size=16, color='#d1d4dc', family='Segoe UI'),
        ),
        height=120 + (rows * 200),
        showlegend=True,
        legend=dict(
            orientation='h',
            y=-0.15 - (0.05 * (rows - 1)),
            x=0.5, xanchor='center',
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='#d1d4dc', size=11),
        ),
        template='plotly_dark',
        hovermode='x unified',
        plot_bgcolor='#1e222d',
        paper_bgcolor='#1e222d',
        font=dict(color='#d1d4dc', family='Segoe UI'),
        margin=dict(l=60, r=40, t=60, b=100),
    )

    # 坐标轴样式
    for i in range(1, rows + 1):
        fig.update_xaxes(
            showgrid=True,
            gridcolor='#363a45',
            gridwidth=1,
            zeroline=False,
            tickfont=dict(color='#787b86', size=10),
            row=i, col=1
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor='#363a45',
            gridwidth=1,
            zeroline=False,
            tickfont=dict(color='#787b86', size=10),
            side='right',
            row=i, col=1
        )

    # Rangeslider
    fig.update_xaxes(rangeslider_visible=True, rangeslider_thickness=0.04, row=rows, col=1)

    return fig


def create_bar_chart(title: str, traces_data: list) -> go.Figure:
    """创建柱状图 - 使用线条模式在深色背景更可见"""
    fig = make_subplots(rows=1, cols=1)

    for trace_name, trace_y, color in traces_data:
        # 使用lines+markers模式，添加明亮的边框线使柱子更可见
        fig.add_trace(
            go.Bar(
                x=trace_y.index,
                y=trace_y.values,
                name=trace_name,
                marker=dict(
                    color=color,
                    line=dict(color=color, width=2),
                    opacity=1.0,
                ),
            )
        )

    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            x=0.5,
            font=dict(size=16, color='#d1d4dc'),
        ),
        height=400,
        showlegend=True,
        legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center'),
        template='plotly_dark',
        hovermode='x unified',
        plot_bgcolor='#1e222d',
        paper_bgcolor='#1e222d',
        font=dict(color='#d1d4dc'),
        margin=dict(l=60, r=40, t=60, b=100),
        barmode='group',
        bargroupgap=0.1,
    )

    fig.update_xaxes(showgrid=True, gridcolor='#363a45', rangeslider_visible=True, rangeslider_thickness=0.04)
    fig.update_yaxes(showgrid=True, gridcolor='#363a45', side='right')

    return fig


def create_comparison_chart(indicators: list, chart_type: str = 'line') -> go.Figure:
    """创建多标的对比图表"""
    if chart_type == 'bar':
        return create_bar_comparison(indicators)
    return create_line_comparison(indicators)


def create_line_comparison(indicators: list, title: str = None) -> go.Figure:
    """创建多标的线图对比"""
    traces_data = []
    colors = list(TICKER_COLORS.values())

    for idx, ind in enumerate(indicators):
        df = load_indicator(ind['filepath'])
        if df is None:
            continue
        col_name = df.columns[0]
        color = TICKER_COLORS.get(ind['ticker'], colors[idx % len(colors)])
        name = f"{TICKER_NAMES.get(ind['ticker'], ind['ticker'])}"
        if ind.get('window'):
            name += f" {ind['window']}日"
        traces_data.append((name, df[col_name], color, 2))

    if not traces_data:
        return None

    chart_title = title or (indicators[0]['name'] if indicators else '对比')
    return create_line_chart(
        title=chart_title,
        traces_data=traces_data
    )


def create_bar_comparison(indicators: list, title: str = None) -> go.Figure:
    """创建多标的柱状对比"""
    traces_data = []
    colors = list(TICKER_COLORS.values())

    for idx, ind in enumerate(indicators):
        df = load_indicator(ind['filepath'])
        if df is None:
            continue
        col_name = df.columns[0]
        color = TICKER_COLORS.get(ind['ticker'], colors[idx % len(colors)])
        name = TICKER_NAMES.get(ind['ticker'], ind['ticker'])
        if ind.get('window'):
            name += f" {ind['window']}日"
        traces_data.append((name, df[col_name], color))

    if not traces_data:
        return None

    chart_title = title or (indicators[0]['name'] if indicators else '对比')
    return create_bar_chart(
        title=chart_title,
        traces_data=traces_data
    )


def create_single_line_chart(title: str, trace_y: pd.Series, color: str, height: int = 400) -> go.Figure:
    """创建单个标的的独立图表"""
    fig = make_subplots(rows=1, cols=1)

    fig.add_trace(
        go.Scatter(
            x=trace_y.index,
            y=trace_y.values,
            mode='lines',
            name=trace_y.name if hasattr(trace_y, 'name') else title,
            line=dict(
                color=color,
                width=2,
                shape='spline',
            ),
            fill='tozeroy',
            fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)',
        )
    )

    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            x=0.5,
            xanchor='center',
            font=dict(size=16, color='#d1d4dc', family='Segoe UI'),
        ),
        height=height,
        showlegend=True,
        legend=dict(
            orientation='h',
            y=-0.15,
            x=0.5, xanchor='center',
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='#d1d4dc', size=11),
        ),
        template='plotly_dark',
        hovermode='x unified',
        plot_bgcolor='#1e222d',
        paper_bgcolor='#1e222d',
        font=dict(color='#d1d4dc', family='Segoe UI'),
        margin=dict(l=60, r=40, t=60, b=100),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor='#363a45',
        gridwidth=1,
        zeroline=False,
        tickfont=dict(color='#787b86', size=10),
        rangeslider_visible=True,
        rangeslider_thickness=0.04,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor='#363a45',
        gridwidth=1,
        zeroline=False,
        tickfont=dict(color='#787b86', size=10),
        side='right',
    )

    return fig


# ==========================================
# HTML生成
# ==========================================

def generate_html(indicators: dict, charts: dict) -> str:
    """生成完整HTML页面"""

    # 获取所有标的
    all_tickers = set()
    for cat, types in indicators.items():
        for ind_list in types.values():
            for ind in ind_list:
                all_tickers.add(ind['ticker'])

    # 标的复选框HTML
    ticker_checkboxes = ''
    for ticker in sorted(all_tickers):
        color = TICKER_COLORS.get(ticker, '#888888')
        name = TICKER_NAMES.get(ticker, ticker)
        ticker_checkboxes += f'''
        <label class="checkbox-item">
          <input type="checkbox" data-ticker="{ticker}" checked>
          <span class="color-dot" style="background: {color}"></span>
          <span class="ticker-name">{name}</span>
        </label>
        '''

    # 指标导航HTML
    indicator_nav = ''
    for category, types in indicators.items():
        indicator_nav += f'<div class="nav-category">{category}</div>'

        # 趋势类
        trend_inds = types.get('趋势', [])
        if trend_inds:
            ma_tickers = set(i['ticker'] for i in trend_inds if i['pattern'] == 'ma')
            for ticker in sorted(ma_tickers):
                color = TICKER_COLORS.get(ticker, '#888888')
                name = TICKER_NAMES.get(ticker, ticker)
                indicator_nav += f'''
                <div class="nav-item" data-chart="ma_{ticker}">
                  <span class="nav-dot" style="background: {color}"></span>
                  <span class="nav-text">{name} 均线</span>
                </div>
                '''

        # 动量类
        mom_inds = types.get('动量', [])
        if mom_inds:
            mom_tickers = set(i['ticker'] for i in mom_inds if i['pattern'] == 'mom')
            for ticker in sorted(mom_tickers):
                color = TICKER_COLORS.get(ticker, '#888888')
                name = TICKER_NAMES.get(ticker, ticker)
                indicator_nav += f'''
                <div class="nav-item" data-chart="mom_{ticker}">
                  <span class="nav-dot" style="background: {color}"></span>
                  <span class="nav-text">{name} 动量</span>
                </div>
                '''

        # 情绪类 - 按标的拆分显示
        sent_inds = types.get('情绪', [])

        # 成交额按标的拆分
        amt_tickers = set(i['ticker'] for i in sent_inds if i['pattern'] == 'amt')
        for ticker in sorted(amt_tickers):
            color = TICKER_COLORS.get(ticker, '#888888')
            name = TICKER_NAMES.get(ticker, ticker)
            indicator_nav += f'''
            <div class="nav-item" data-chart="amt_{ticker}">
              <span class="nav-dot" style="background: {color}"></span>
              <span class="nav-text">{name} 成交额</span>
            </div>
            '''

        # 涨跌幅绝对值按标的拆分
        pchg_tickers = set(i['ticker'] for i in sent_inds if i['pattern'] == 'pchg_abs')
        for ticker in sorted(pchg_tickers):
            color = TICKER_COLORS.get(ticker, '#888888')
            name = TICKER_NAMES.get(ticker, ticker)
            indicator_nav += f'''
            <div class="nav-item" data-chart="pchg_{ticker}">
              <span class="nav-dot" style="background: {color}"></span>
              <span class="nav-text">{name} 涨跌幅</span>
            </div>
            '''

        # 相对强弱 - 每个对比对单独一个图
        rs_inds_grouped = {}
        for i in sent_inds:
            if i['pattern'] == 'rs':
                key = f"{i['ticker_a']}_vs_{i['ticker_b']}"
                rs_inds_grouped[key] = i

        for pair_key, ind in sorted(rs_inds_grouped.items()):
            name_a = TICKER_NAMES.get(ind['ticker_a'], ind['ticker_a'])
            name_b = TICKER_NAMES.get(ind['ticker_b'], ind['ticker_b'])
            color = TICKER_COLORS.get(ind['ticker_a'], '#888888')
            indicator_nav += f'''
            <div class="nav-item" data-chart="rs_{pair_key}">
              <span class="nav-dot" style="background: {color}"></span>
              <span class="nav-text">{name_a} vs {name_b}</span>
            </div>
            '''

    # 图表数据JSON
    charts_json = {}
    for chart_id, fig in charts.items():
        if fig:
            charts_json[chart_id] = json.loads(fig.to_json())

    charts_json_str = json.dumps(charts_json, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>大类资产配置指标监控面板</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --bg-primary: #131722;
            --bg-secondary: #1e222d;
            --bg-tertiary: #2a2e39;
            --border-color: #363a45;
            --text-primary: #d1d4dc;
            --text-secondary: #787b86;
            --text-muted: #5c6070;
            --positive: #26a69a;
            --negative: #ef5350;
            --accent: #2979ff;
        }}

        body {{
            font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            overflow: hidden;
        }}

        /* 顶部工具栏 */
        .toolbar {{
            height: 56px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
        }}

        .toolbar-left {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .logo {{
            font-size: 24px;
        }}

        .toolbar-title {{
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .toolbar-center {{
            display: flex;
            gap: 8px;
        }}

        .range-btn {{
            padding: 6px 14px;
            border: 1px solid var(--border-color);
            background: transparent;
            color: var(--text-secondary);
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .range-btn:hover {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }}

        .range-btn.active {{
            background: var(--accent);
            border-color: var(--accent);
            color: white;
        }}

        .toolbar-right {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .update-time {{
            font-size: 12px;
            color: var(--text-muted);
        }}

        .refresh-btn {{
            width: 36px;
            height: 36px;
            border: 1px solid var(--border-color);
            background: transparent;
            color: var(--text-secondary);
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.2s;
        }}

        .refresh-btn:hover {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }}

        /* 主容器 */
        .main-container {{
            display: flex;
            height: calc(100vh - 56px);
            margin-top: 56px;
        }}

        /* 侧边栏 */
        .sidebar {{
            width: 240px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            overflow-y: auto;
            flex-shrink: 0;
        }}

        .sidebar-section {{
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
        }}

        .section-title {{
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }}

        .checkbox-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
            cursor: pointer;
            font-size: 13px;
            color: var(--text-primary);
        }}

        .checkbox-item:hover {{
            color: var(--accent);
        }}

        .checkbox-item input {{
            display: none;
        }}

        .color-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }}

        .checkbox-item input:checked ~ .color-dot {{
            box-shadow: 0 0 0 3px rgba(41, 121, 255, 0.3);
        }}

        .nav-category {{
            font-size: 11px;
            font-weight: 600;
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 16px 16px 8px;
        }}

        .nav-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 16px;
            cursor: pointer;
            font-size: 13px;
            color: var(--text-secondary);
            border-left: 3px solid transparent;
            transition: all 0.2s;
        }}

        .nav-item:hover {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }}

        .nav-item.active {{
            background: rgba(41, 121, 255, 0.1);
            border-left-color: var(--accent);
            color: var(--accent);
        }}

        .nav-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }}

        .nav-icon {{
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg-tertiary);
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            color: var(--text-muted);
        }}

        .nav-item.active .nav-icon {{
            background: rgba(41, 121, 255, 0.2);
            color: var(--accent);
        }}

        /* 主内容区 */
        .content {{
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            background: var(--bg-primary);
        }}

        /* 图表卡片 */
        .chart-card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
            border: 1px solid var(--border-color);
        }}

        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
        }}

        .chart-title {{
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .chart-legend {{
            display: flex;
            gap: 16px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--text-secondary);
        }}

        .legend-line {{
            width: 16px;
            height: 3px;
            border-radius: 2px;
        }}

        .chart-container {{
            height: 400px;
            width: 100%;
        }}

        /* 欢迎页 */
        .welcome {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 400px;
            text-align: center;
            color: var(--text-muted);
        }}

        .welcome-icon {{
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }}

        .welcome h2 {{
            font-size: 18px;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }}

        .welcome p {{
            font-size: 13px;
        }}

        /* 滚动条 */
        ::-webkit-scrollbar {{
            width: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: var(--bg-primary);
        }}

        ::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 4px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: var(--text-muted);
        }}
    </style>
</head>
<body>
    <!-- 工具栏 -->
    <header class="toolbar">
        <div class="toolbar-left">
            <span class="logo">📊</span>
            <span class="toolbar-title">大类资产配置指标监控</span>
        </div>
        <div class="toolbar-center">
            <button class="range-btn" data-range="1M">1M</button>
            <button class="range-btn" data-range="3M">3M</button>
            <button class="range-btn active" data-range="6M">6M</button>
            <button class="range-btn" data-range="YTD">YTD</button>
            <button class="range-btn" data-range="1Y">1Y</button>
            <button class="range-btn" data-range="ALL">All</button>
        </div>
        <div class="toolbar-right">
            <span class="update-time">更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
            <button class="refresh-btn" onclick="location.reload()">&#8635;</button>
        </div>
    </header>

    <!-- 主容器 -->
    <div class="main-container">
        <!-- 侧边栏 -->
        <aside class="sidebar">
            <div class="sidebar-section">
                <div class="section-title">标的</div>
                {ticker_checkboxes}
            </div>

            <div class="sidebar-section">
                <div class="section-title">指标</div>
                {indicator_nav}
            </div>
        </aside>

        <!-- 主内容 -->
        <main class="content">
            <div class="chart-card">
                <div class="chart-header">
                    <h2 class="chart-title" id="chartTitle">选择指标查看</h2>
                    <div class="chart-legend" id="chartLegend"></div>
                </div>
                <div class="chart-container" id="mainChart">
                    <div class="welcome">
                        <div class="welcome-icon">&#128200;</div>
                        <h2>大类资产配置指标监控</h2>
                        <p>从左侧选择指标进行查看</p>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        // 图表数据
        const chartsData = {charts_json_str};

        // 当前图表ID
        let currentChartId = null;

        // 当前时间范围
        let currentRange = '6M';

        // 计算日期范围
        function getDateRange(range) {{
            const now = new Date();
            let startDate;

            switch(range) {{
                case '1M':
                    startDate = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
                    break;
                case '3M':
                    startDate = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
                    break;
                case '6M':
                    startDate = new Date(now.getFullYear(), now.getMonth() - 6, now.getDate());
                    break;
                case 'YTD':
                    startDate = new Date(now.getFullYear(), 0, 1);
                    break;
                case '1Y':
                    startDate = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
                    break;
                case 'ALL':
                default:
                    return null; // 返回null表示显示全部
            }}
            return startDate;
        }}

        // 初始化
        document.addEventListener('DOMContentLoaded', function() {{
            // 绑定指标导航点击
            document.querySelectorAll('.nav-item').forEach(item => {{
                item.addEventListener('click', function() {{
                    // 移除其他激活状态
                    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                    // 激活当前
                    this.classList.add('active');

                    // 加载图表
                    const chartId = this.dataset.chart;
                    loadChart(chartId);
                }});
            }});

            // 绑定时间范围按钮
            document.querySelectorAll('.range-btn').forEach(btn => {{
                btn.addEventListener('click', function() {{
                    document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    currentRange = this.dataset.range;
                    // 应用时间范围筛选
                    applyTimeRange();
                }});
            }});

            // 自动点击第一个指标
            const firstNavItem = document.querySelector('.nav-item');
            if (firstNavItem) {{
                firstNavItem.click();
            }}
        }});

        // 应用时间范围
        function applyTimeRange() {{
            if (!currentChartId) return;

            const container = document.getElementById('mainChart');
            const chartConfig = chartsData[currentChartId];
            if (!chartConfig) return;

            const startDate = getDateRange(currentRange);

            if (startDate) {{
                // 转换日期为毫秒时间戳
                const startMs = startDate.getTime();

                // 找到第一个trace的x轴数据（日期）
                const trace = chartConfig.data[0];
                if (trace && trace.x) {{
                    // 找到第一个大于startDate的索引
                    let visibleStart = 0;
                    for (let i = 0; i < trace.x.length; i++) {{
                        const dateMs = new Date(trace.x[i]).getTime();
                        if (dateMs >= startMs) {{
                            visibleStart = i;
                            break;
                        }}
                    }}

                    // 计算可见范围
                    const xAxis = chartConfig.layout.xaxis;
                    const rangeStart = trace.x[visibleStart];
                    const rangeEnd = trace.x[trace.x.length - 1];

                    // 更新布局的x轴范围
                    const newLayout = {{
                        ...chartConfig.layout,
                        xaxis: {{
                            ...chartConfig.layout.xaxis,
                            range: [rangeStart, rangeEnd]
                        }}
                    }};

                    Plotly.relayout(container, newLayout);
                }}
            }} else {{
                // 显示全部 - 移除范围限制
                const xAxis = chartConfig.layout.xaxis;
                if (xAxis && xAxis.range) {{
                    const newLayout = {{
                        ...chartConfig.layout,
                        xaxis: {{
                            ...chartConfig.layout.xaxis,
                            range: [xAxis.range[0], xAxis.range[1]]
                        }}
                    }};
                    // 恢复完整范围
                    Plotly.relayout(container, 'xaxis.range', null);
                }}
            }}
        }}

        // 加载图表
        function loadChart(chartId) {{
            const container = document.getElementById('mainChart');
            const titleEl = document.getElementById('chartTitle');
            const legendEl = document.getElementById('chartLegend');

            if (!chartsData[chartId]) {{
                container.innerHTML = '<div class="welcome"><div class="welcome-icon">&#9888;</div><h2>图表不存在</h2></div>';
                return;
            }}

            // 更新标题
            const navItem = document.querySelector(`[data-chart="${{chartId}}"]`);
            if (navItem) {{
                titleEl.textContent = navItem.querySelector('.nav-text').textContent;
            }}

            // 清除图例
            legendEl.innerHTML = '';

            // 渲染图表
            const chartConfig = chartsData[chartId];

            Plotly.newPlot(container, chartConfig.data, chartConfig.layout, {{
                responsive: true,
                displayModeBar: true,
                scrollZoom: true,
                modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                displaylogo: false,
                modeBarButtonsToAdd: ['drawline', 'eraseshape'],
            }});

            // 更新图例
            if (chartConfig.data && chartConfig.data.length > 0) {{
                const colors = ['#00b8a9', '#f75b5b', '#f7cc35', '#4caf50', '#9c27b0', '#2196f3'];
                chartConfig.data.forEach((trace, i) => {{
                    if (trace.name) {{
                        const color = colors[i % colors.length];
                        legendEl.innerHTML += (
                            '<span class="legend-item">' +
                            '<span class="legend-line" style="background: ' + color + '"></span>' +
                            trace.name +
                            '</span>'
                        );
                    }}
                }});
            }}

            currentChartId = chartId;

            // 应用当前时间范围
            applyTimeRange();
        }}
    </script>
</body>
</html>'''

    return html


def create_dashboard():
    """主函数：创建仪表板"""
    print("=" * 60)
    print("AA-Model Dashboard V4.0")
    print("=" * 60)

    print("\n[Step 1/3] Scanning indicator library...")
    indicators = discover_available_indicators(OUTPUT_DIR)

    if not indicators:
        print("[ERROR] No valid indicators found.")
        return

    print("\n[Step 2/3] Creating charts...")

    charts = {}
    all_tickers = set()
    for cat, types in indicators.items():
        for ind_list in types.values():
            for ind in ind_list:
                all_tickers.add(ind['ticker'])

    # 均线图表
    for ticker in sorted(all_tickers):
        trend_inds = [i for i in indicators.get('量价类', {}).get('趋势', [])
                     if i['pattern'] == 'ma' and i['ticker'] == ticker]
        if trend_inds:
            fig = create_line_comparison(trend_inds)
            if fig:
                charts[f'ma_{ticker}'] = fig

    # 动量图表
    for ticker in sorted(all_tickers):
        mom_inds = [i for i in indicators.get('量价类', {}).get('动量', [])
                    if i['pattern'] == 'mom' and i['ticker'] == ticker]
        if mom_inds:
            fig = create_line_comparison(mom_inds)
            if fig:
                charts[f'mom_{ticker}'] = fig

    # 情绪图表 - 按标的拆分
    sent_inds = indicators.get('量价类', {}).get('情绪', [])

    # 成交额 - 每个标的单独一个图表
    amt_inds = [i for i in sent_inds if i['pattern'] == 'amt']
    amt_tickers = set(i['ticker'] for i in amt_inds)
    for ticker in sorted(amt_tickers):
        ticker_amt = [i for i in amt_inds if i['ticker'] == ticker]
        if ticker_amt:
            name = TICKER_NAMES.get(ticker, ticker)
            charts[f'amt_{ticker}'] = create_bar_comparison(
                ticker_amt,
                title=f'{name} 成交额'
            )

    # 涨跌幅绝对值 - 每个标的单独一个图表
    pchg_inds = [i for i in sent_inds if i['pattern'] == 'pchg_abs']
    pchg_tickers = set(i['ticker'] for i in pchg_inds)
    for ticker in sorted(pchg_tickers):
        ticker_pchg = [i for i in pchg_inds if i['ticker'] == ticker]
        if ticker_pchg:
            name = TICKER_NAMES.get(ticker, ticker)
            charts[f'pchg_{ticker}'] = create_bar_comparison(
                ticker_pchg,
                title=f'{name} 涨跌幅绝对值'
            )

    # 相对强弱 - 每个对比对单独一个图表
    rs_inds = [i for i in sent_inds if i['pattern'] == 'rs']
    for ind in rs_inds:
        pair_key = f"{ind['ticker_a']}_vs_{ind['ticker_b']}"
        name_a = TICKER_NAMES.get(ind['ticker_a'], ind['ticker_a'])
        name_b = TICKER_NAMES.get(ind['ticker_b'], ind['ticker_b'])
        charts[f'rs_{pair_key}'] = create_line_comparison(
            [ind],
            title=f'{name_a} vs {name_b} 相对强弱'
        )

    print(f"[INFO] Created {len(charts)} charts")

    print("\n[Step 3/3] Generating HTML...")
    html = generate_html(indicators, charts)

    output_path = os.path.join(os.path.dirname(OUTPUT_DIR), OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[OK] Report: {output_path}")
    print("[INFO] Open in browser to view")

    return output_path


if __name__ == "__main__":
    create_dashboard()
