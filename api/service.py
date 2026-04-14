"""数据服务"""
import json
import os
from typing import Dict, List, Optional
from functools import lru_cache

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.utils import PlotlyJSONEncoder

# 导入配置
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, get_ticker_color, get_ticker_name, INDICATOR_PATTERNS
from data.discover import discover_indicators, classify_indicator
from data.loader import load_indicator


class ChartService:
    """图表数据服务"""

    # 默认颜色
    DEFAULT_COLORS = ['#00b8a9', '#f75b5b', '#f7cc35', '#4caf50', '#9c27b0', '#2196f3']

    # 时间窗口映射（交易日数量）
    TIME_WINDOWS = {
        '6M': 126,   # 约6个月
        '1Y': 252,   # 约1年
        '3Y': 756,   # 约3年
        '5Y': 1260,  # 约5年
        'ALL': None  # 全数据（不使用滚动）
    }

    # 图表数据缓存（避免重复计算）
    _chart_cache: Dict[str, Dict] = {}

    @classmethod
    def clear_cache(cls):
        """清除图表缓存"""
        cls._chart_cache.clear()

    @classmethod
    def _get_ticker_display_name(cls, ticker: str) -> str:
        """获取用于显示的标的名称（处理 _vs_ 格式）"""
        if '_vs_' in ticker:
            parts = ticker.split('_vs_')
            name_a = get_ticker_name(parts[0])
            name_b = get_ticker_name(parts[1])
            return f"{name_a} vs {name_b}"
        return get_ticker_name(ticker)

    @classmethod
    def _get_ticker_display_color(cls, ticker: str) -> str:
        """获取标的颜色（处理 _vs_ 格式）"""
        if '_vs_' in ticker:
            first_ticker = ticker.split('_vs_')[0]
            return get_ticker_color(first_ticker) or '#888888'
        return get_ticker_color(ticker)

    @classmethod
    def get_indicators(cls) -> Dict:
        """获取所有指标元数据"""
        indicators = discover_indicators(OUTPUT_DIR)

        # 转换为API格式
        result = {}
        for category, types in indicators.items():
            result[category] = {}
            for type_name, ind_list in types.items():
                result[category][type_name] = [
                    {
                        'id': cls._make_chart_id(i),
                        'name': i['name'],
                        'pattern': i['pattern'],
                        'ticker': i['ticker'],
                        'category': category,
                        'type': type_name,
                        'window': i.get('window'),
                        'is_cross': i.get('is_cross', False),
                    }
                    for i in ind_list
                ]

        return result

    @classmethod
    def get_tickers(cls) -> List[Dict]:
        """获取所有标的"""
        indicators = discover_indicators(OUTPUT_DIR)

        all_tickers = set()
        for cat, types in indicators.items():
            for ind_list in types.values():
                for ind in ind_list:
                    all_tickers.add(ind['ticker'])

        return [
            {
                'code': ticker,
                'name': cls._get_ticker_display_name(ticker),
                'color': cls._get_ticker_display_color(ticker),
            }
            for ticker in sorted(all_tickers)
        ]

    @classmethod
    def _make_chart_id(cls, ind: Dict) -> str:
        """生成图表ID（包含窗口信息确保唯一性）"""
        pattern = ind['pattern']
        ticker = ind['ticker']
        window = ind.get('window')

        if ind.get('is_cross'):
            return f"{pattern}_{ticker}"
        else:
            if window:
                return f"{pattern}_{ticker}_{window}d"
            return f"{pattern}_{ticker}"

    @classmethod
    def get_chart_data(cls, chart_id: str, rolling_window: str = '1Y') -> Optional[Dict]:
        # Get chart data with specified rolling window
        # Args:
        #   chart_id: Chart ID (format: pattern_ticker)
        #   rolling_window: Rolling window period ('6M', '1Y', '3Y', '5Y', 'ALL')
        # Returns:
        #   Dictionary containing data and layout
        # Check cache (key includes rolling window)
        cache_key = f"{chart_id}_{rolling_window}"
        if cache_key in cls._chart_cache:
            return cls._chart_cache[cache_key]

        indicators = discover_indicators(OUTPUT_DIR)

        # 找到对应的指标
        target_ind = None
        for cat, types in indicators.items():
            for type_name, ind_list in types.items():
                for ind in ind_list:
                    if cls._make_chart_id(ind) == chart_id:
                        target_ind = ind
                        break
                if target_ind:
                    break
            if target_ind:
                break

        if not target_ind:
            return None

        # 加载数据
        df = load_indicator(target_ind['filepath'])
        if df is None:
            return None

        # 获取颜色
        ticker = target_ind['ticker']
        color = cls._get_ticker_display_color(ticker) or cls.DEFAULT_COLORS[0]

        # 构建标题
        name = cls._get_ticker_display_name(ticker)
        window = target_ind.get('window')
        title = f"{name} {target_ind['name']}"
        if window:
            title = f"{name} {window}日{target_ind['name']}"

        # 创建图表（传入滚动窗口参数）
        fig = cls._create_chart(target_ind['pattern'], title, df, color, rolling_window)

        if fig is None:
            return None

        # 转换为字典
        # 注意：避免 fig.to_json() 产生 {dtype,bdata} 的压缩数组格式，前端 plotly.js 可能解码异常导致"直线/空图"。
        # 这里使用 to_plotly_json + PlotlyJSONEncoder，配合我们在 trace 中将 x/y 强制转为 list。
        fig_json = json.loads(json.dumps(fig.to_plotly_json(), cls=PlotlyJSONEncoder))
        result = {
            'id': chart_id,
            'title': title,
            'rolling_window': rolling_window,
            'data': fig_json['data'],
            'layout': fig_json['layout'],
        }

        # 存入缓存
        cls._chart_cache[cache_key] = result
        return result

    @classmethod
    def _create_chart(cls, pattern: str, title: str, df: pd.DataFrame, color: str, rolling_window: str = '1Y') -> Optional[go.Figure]:
        """根据指标类型创建图表"""
        if df.empty:
            return None

        col_name = df.columns[0]

        if pattern in ['ma', 'mom', 'ma_dev', 'vol', 'rsi', 'high_new', 'low_new', 'return_acf1', 'iv', 'erp']:
            # 线图
            return cls._create_line_chart(title, df, col_name, color, rolling_window)
        elif pattern in ['amt', 'pchg_abs']:
            # 柱状图
            return cls._create_bar_chart(title, df, col_name, color)
        elif pattern == 'rs':
            # 相对强弱 - 线图
            return cls._create_line_chart(title, df, col_name, color, rolling_window)
        elif pattern == 'rt':
            # 相对换手率 - 线图
            return cls._create_line_chart(title, df, col_name, color, rolling_window)

        return None

    @classmethod
    def _create_line_chart(cls, title: str, df: pd.DataFrame, col_name: str, color: str, rolling_window: str = '1Y') -> go.Figure:
        """创建增强线图 - 工业实用主义设计"""
        fig = make_subplots(rows=1, cols=1)

        x_vals = df.index.astype(str).tolist()
        y_vals = df[col_name].tolist()

        # 根据数据范围确定Y轴格式
        tick_fmt = cls._get_tick_format(y_vals)

        # 获取时间窗口对应的交易日数量
        window_size = cls.TIME_WINDOWS.get(rolling_window)
        is_all = window_size is None  # ALL 模式不使用滚动

        # 计算滚动统计信息（用于动态标准差带）
        if is_all:
            # ALL 模式：使用全数据计算均值和标准差（不滚动）
            rolling_mean = pd.Series([df[col_name].mean()] * len(y_vals))
            rolling_std = pd.Series([df[col_name].std()] * len(y_vals))
        else:
            # 使用时间窗口滚动计算
            window_size = min(window_size, len(y_vals)) if len(y_vals) > 0 else 1
            if window_size > 1:
                rolling_mean = df[col_name].rolling(window=window_size, min_periods=1).mean()
                rolling_std = df[col_name].rolling(window=window_size, min_periods=1).std()
            else:
                rolling_mean = df[col_name]
                rolling_std = pd.Series([0] * len(y_vals))

        # 计算全局统计信息
        mean_val = df[col_name].mean()
        std_val = df[col_name].std()
        y_min = df[col_name].min()
        y_max = df[col_name].max()

        # 0. 添加动态标准差带（±1σ 和 ±2σ）
        if len(y_vals) > 5 and std_val > 0:
            # +2σ 带（最外层）- 加粗虚线
            upper_2sigma = (rolling_mean + 2 * rolling_std).tolist()
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=upper_2sigma,
                    fill=None,
                    line=dict(color='rgba(255, 152, 0, 0.8)', width=1.5, dash='dot'),
                    name='+2σ',
                    showlegend=True,
                    hoverinfo='skip',
                )
            )

            # +1σ 带 - 加粗虚线
            upper_1sigma = (rolling_mean + rolling_std).tolist()
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=upper_1sigma,
                    fill='tonexty',
                    fillcolor=cls._hex_to_rgba(color, 0.12),
                    line=dict(color='rgba(255, 193, 7, 0.8)', width=1.5, dash='dash'),
                    name='+1σ',
                    showlegend=True,
                    hoverinfo='skip',
                )
            )

            # -1σ 带 - 加粗虚线
            lower_1sigma = (rolling_mean - rolling_std).tolist()
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=lower_1sigma,
                    fill='tonexty',
                    fillcolor=cls._hex_to_rgba(color, 0.12),
                    line=dict(color='rgba(255, 193, 7, 0.8)', width=1.5, dash='dash'),
                    name='-1σ',
                    showlegend=True,
                    hoverinfo='skip',
                )
            )

            # -2σ 带（最内层）- 加粗虚线
            lower_2sigma = (rolling_mean - 2 * rolling_std).tolist()
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=lower_2sigma,
                    fill='tonexty',
                    fillcolor=cls._hex_to_rgba(color, 0.08),
                    line=dict(color='rgba(255, 152, 0, 0.8)', width=1.5, dash='dot'),
                    name='-2σ',
                    showlegend=True,
                    hoverinfo='skip',
                )
            )

            # 均线（滚动均值）
            rolling_mean_vals = rolling_mean.tolist()
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=rolling_mean_vals,
                    mode='lines',
                    name='均线',
                    line=dict(
                        color='#FF9800',
                        width=2,
                        shape='spline',
                        smoothing=0.6,
                    ),
                    hoverlabel=dict(
                        bgcolor='rgba(10, 12, 16, 0.9)',
                        font=dict(color='#e3e7f1', family='Inter'),
                        bordercolor='#FF9800',
                    ),
                    hovertemplate='均线: %{y:' + tick_fmt['hoverformat'] + '}<extra></extra>',
                )
            )

        # 1. 添加主数据线 - 增强工业设计
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='lines',
                name=df[col_name].name if hasattr(df[col_name], 'name') else title,
                line=dict(
                    color=color,
                    width=2.5,
                    shape='spline',
                    smoothing=0.8,
                ),
                # 渐变填充（从颜色到透明）- 使用半透明单色
                fill='tozeroy',
                fillcolor=cls._hex_to_rgba(color, 0.25),
                hoverlabel=dict(
                    bgcolor='rgba(10, 12, 16, 0.9)',
                    font=dict(color='#e3e7f1', family='Inter'),
                    bordercolor=color,
                ),
                hovertemplate='%{x}<br>%{y:' + tick_fmt['hoverformat'] + '}<extra></extra>',
            )
        )

        # 2. 添加均值线（工业感虚线）
        if len(y_vals) > 0:
            # 根据数据范围确定标注格式
            fmt = cls._get_tick_format(y_vals)
            mean_text = f"均值: {mean_val:{fmt['tickformat']}}"

            fig.add_hline(
                y=mean_val,
                line=dict(
                    color='rgba(139, 147, 167, 0.6)',  # 工业中性色
                    width=1.5,
                    dash='dash',
                ),
                annotation=dict(
                    text=mean_text,
                    font=dict(color='#8b93a7', size=11),
                    bgcolor='rgba(20, 23, 31, 0.9)',
                    bordercolor='#3a4052',
                    borderwidth=1,
                    borderpad=4,
                    showarrow=False,
                    x=1.0,
                    xanchor='right',
                    xref='paper',
                    yanchor='bottom',
                    yref='y',
                    y=mean_val,
                ),
            )

        # 工业实用主义布局
        fig.update_layout(
            title=dict(
                text=f'<b>{title}</b>',
                x=0.5,
                xanchor='center',
                font=dict(
                    size=20,
                    color='#e3e7f1',  # 工业主文本色
                    family='Space Grotesk, SF Pro Display, -apple-system, sans-serif',
                ),
                pad=dict(t=10, b=20),
            ),
            autosize=True,
            showlegend=True,
            legend=dict(
                orientation='h',
                y=-0.15,
                x=0.5,
                xanchor='center',
                bgcolor='rgba(10, 12, 16, 0.9)',
                bordercolor='#3a4052',
                borderwidth=1,
                font=dict(color='#e3e7f1', size=14, family='Inter, sans-serif'),
                itemsizing='constant',
            ),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='rgba(10, 12, 16, 0.9)',
                font=dict(color='#e3e7f1', size=12, family='Inter'),
                bordercolor='#3a4052',
                align='left',
            ),
            plot_bgcolor='#14171f',  # 工业表面提升色
            paper_bgcolor='#0a0c10',  # 工业基础表面色
            font=dict(
                color='#8b93a7',  # 工业次文本色
                family='Inter, SF Pro Text, -apple-system, sans-serif',
                size=12,
            ),
            margin=dict(l=70, r=70, t=80, b=150),
            separators=',',
            xaxis_rangeslider_visible=True,
            xaxis_rangeslider_thickness=0.08,
            xaxis_rangeslider_bgcolor='rgba(20, 23, 31, 0.5)',
        )

        # X轴 - 工业网格设计
        fig.update_xaxes(
            showgrid=True,
            gridcolor='#2a2f3d',  # 工业网格线色
            gridwidth=1,
            zeroline=False,
            rangeslider_visible=True,
            rangeslider_thickness=0.08,
            rangeslider_bgcolor='rgba(20, 23, 31, 0.5)',
            tickfont=dict(color='#5a6275', size=11),  # 工业减弱文本
            tickangle=-45,
            showline=True,
            linecolor='#3a4052',
            linewidth=1,
            mirror=True,
            spikecolor='#4a5168',
            spikethickness=1,
            spikemode='across',
            spikedash='solid',
        )

        # Y轴 - 工业网格设计（动态格式）
        tick_fmt = cls._get_tick_format(y_vals)
        fig.update_yaxes(
            showgrid=True,
            gridcolor='#2a2f3d',  # 工业网格线色
            gridwidth=1,
            zeroline=False,
            side='right',
            autorange=True,
            tickfont=dict(color='#5a6275', size=11),
            showline=True,
            linecolor='#3a4052',
            linewidth=1,
            mirror=True,
            separatethousands=tick_fmt['separatethousands'],
            tickformat=tick_fmt['tickformat'],
            hoverformat=tick_fmt['hoverformat'],
        )

        return fig

    @classmethod
    def _create_bar_chart(cls, title: str, df: pd.DataFrame, col_name: str, color: str) -> go.Figure:
        """创建增强柱状图 - 工业实用主义设计"""
        fig = make_subplots(rows=1, cols=1)

        x_vals = df.index.astype(str).tolist()
        y_vals = df[col_name].tolist()

        # 根据数据范围确定Y轴格式
        tick_fmt = cls._get_tick_format(y_vals)

        # 计算统计信息
        mean_val = df[col_name].mean()
        positive_color = cls._hex_to_rgba('#00e676', 0.8)  # 语义正向色
        negative_color = cls._hex_to_rgba('#ff4081', 0.8)  # 语义负向色

        # 根据数值正负设置柱状图颜色
        marker_colors = [positive_color if y >= 0 else negative_color for y in y_vals]

        fig.add_trace(
            go.Bar(
                x=x_vals,
                y=y_vals,
                name=df[col_name].name if hasattr(df[col_name], 'name') else title,
                marker=dict(
                    color=marker_colors,
                    line=dict(
                        color=[color if y >= 0 else '#ff4081' for y in y_vals],
                        width=1.5,
                    ),
                    opacity=0.9,
                ),
                hovertemplate='%{x}<br>%{y:' + tick_fmt['hoverformat'] + '}<extra></extra>',
            )
        )

        # 添加均值线
        if len(y_vals) > 0:
            fmt = cls._get_tick_format(y_vals)
            fig.add_hline(
                y=mean_val,
                line=dict(
                    color='rgba(139, 147, 167, 0.6)',  # 工业中性色
                    width=1.5,
                    dash='dash',
                ),
                annotation=dict(
                    text=f"均值: {mean_val:{fmt['tickformat']}}",
                    font=dict(color='#8b93a7', size=11),
                    bgcolor='rgba(20, 23, 31, 0.9)',
                    bordercolor='#3a4052',
                    borderwidth=1,
                    borderpad=4,
                    showarrow=False,
                    x=1.0,
                    xanchor='right',
                    xref='paper',
                    yanchor='bottom',
                    yref='y',
                    y=mean_val,
                ),
            )

        # Y轴格式
        fig.update_yaxes(
            showgrid=True,
            gridcolor='#2a2f3d',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='rgba(58, 64, 82, 0.5)',
            zerolinewidth=1,
            side='right',
            autorange=True,
            tickfont=dict(color='#5a6275', size=11),
            showline=True,
            linecolor='#3a4052',
            linewidth=1,
            mirror=True,
            separatethousands=tick_fmt['separatethousands'],
            tickformat=tick_fmt['tickformat'],
            hoverformat=tick_fmt['hoverformat'],
        )

        return fig

    @staticmethod
    def _get_tick_format(y_vals: list) -> dict:
        """根据数据范围确定合适的Y轴格式

        Args:
            y_vals: Y轴数据列表

        Returns:
            包含 tickformat, hoverformat, separatethousands 的字典
        """
        if not y_vals:
            return {'tickformat': '.2f', 'hoverformat': '.2f', 'separatethousands': False}

        y_min = min(y_vals)
        y_max = max(y_vals)
        y_range = y_max - y_min if y_max != y_min else 1

        # 大数值（>10000）使用千分位，不显示小数
        if y_max > 10000:
            return {'tickformat': ',.0f', 'hoverformat': ',.2f', 'separatethousands': True}

        # 中等数值（100-10000）使用千分位，2位小数
        if y_max >= 100:
            return {'tickformat': ',.2f', 'hoverformat': ',.2f', 'separatethousands': True}

        # 小数值或百分比（<100）不需千分位，2位小数
        return {'tickformat': '.2f', 'hoverformat': '.2f', 'separatethousands': False}

    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
        """HEX颜色转RGBA字符串"""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return f'rgba({r}, {g}, {b}, {alpha})'
