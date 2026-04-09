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
    def get_chart_data(cls, chart_id: str) -> Optional[Dict]:
        """获取指定图表的完整数据

        Args:
            chart_id: 图表ID，格式: pattern_ticker (如 ma_000300.SH)

        Returns:
            包含 data 和 layout 的字典
        """
        # 检查缓存
        if chart_id in cls._chart_cache:
            return cls._chart_cache[chart_id]

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

        # 创建图表
        fig = cls._create_chart(target_ind['pattern'], title, df, color)

        if fig is None:
            return None

        # 转换为字典
        # 注意：避免 fig.to_json() 产生 {dtype,bdata} 的压缩数组格式，前端 plotly.js 可能解码异常导致“直线/空图”。
        # 这里使用 to_plotly_json + PlotlyJSONEncoder，配合我们在 trace 中将 x/y 强制转为 list。
        fig_json = json.loads(json.dumps(fig.to_plotly_json(), cls=PlotlyJSONEncoder))
        result = {
            'id': chart_id,
            'title': title,
            'data': fig_json['data'],
            'layout': fig_json['layout'],
        }

        # 存入缓存
        cls._chart_cache[chart_id] = result
        return result

    @classmethod
    def _create_chart(cls, pattern: str, title: str, df: pd.DataFrame, color: str) -> Optional[go.Figure]:
        """根据指标类型创建图表"""
        if df.empty:
            return None

        col_name = df.columns[0]

        if pattern in ['ma', 'mom', 'ma_dev', 'vol', 'rsi']:
            # 线图
            return cls._create_line_chart(title, df, col_name, color)
        elif pattern in ['amt', 'pchg_abs']:
            # 柱状图
            return cls._create_bar_chart(title, df, col_name, color)
        elif pattern == 'rs':
            # 相对强弱 - 线图
            return cls._create_line_chart(title, df, col_name, color)
        elif pattern == 'rt':
            # 相对换手率 - 线图
            return cls._create_line_chart(title, df, col_name, color)

        return None

    @classmethod
    def _create_line_chart(cls, title: str, df: pd.DataFrame, col_name: str, color: str) -> go.Figure:
        """创建线图"""
        fig = make_subplots(rows=1, cols=1)

        x_vals = df.index.astype(str).tolist()
        y_vals = df[col_name].tolist()
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='lines',
                name=df[col_name].name if hasattr(df[col_name], 'name') else title,
                line=dict(
                    color=color,
                    width=2,
                    shape='spline',
                ),
                fill='tozeroy',
                fillcolor=cls._hex_to_rgba(color, 0.1),
            )
        )

        fig.update_layout(
            title=dict(
                text=f'<b>{title}</b>',
                x=0.5,
                xanchor='center',
                font=dict(size=16, color='#d1d4dc', family='Segoe UI'),
            ),
            autosize=True,
            showlegend=True,
            legend=dict(orientation='h', y=-0.15, x=0.5, xanchor='center'),
            template='plotly_dark',
            hovermode='x unified',
            plot_bgcolor='#1e222d',
            paper_bgcolor='#1e222d',
            font=dict(color='#d1d4dc', family='Segoe UI'),
            margin=dict(l=60, r=40, t=60, b=80),
        )

        fig.update_xaxes(
            showgrid=True,
            gridcolor='#363a45',
            rangeslider_visible=True,
            rangeslider_thickness=0.04,
        )
        fig.update_yaxes(showgrid=True, gridcolor='#363a45', side='right', autorange=True)

        return fig

    @classmethod
    def _create_bar_chart(cls, title: str, df: pd.DataFrame, col_name: str, color: str) -> go.Figure:
        """创建柱状图"""
        fig = make_subplots(rows=1, cols=1)

        x_vals = df.index.astype(str).tolist()
        y_vals = df[col_name].tolist()
        fig.add_trace(
            go.Bar(
                x=x_vals,
                y=y_vals,
                name=df[col_name].name if hasattr(df[col_name], 'name') else title,
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
            autosize=True,
            showlegend=True,
            legend=dict(orientation='h', y=-0.15, x=0.5, xanchor='center'),
            template='plotly_dark',
            hovermode='x unified',
            plot_bgcolor='#1e222d',
            paper_bgcolor='#1e222d',
            font=dict(color='#d1d4dc'),
            margin=dict(l=60, r=40, t=60, b=80),
            barmode='group',
            bargroupgap=0.1,
        )

        fig.update_xaxes(showgrid=True, gridcolor='#363a45', rangeslider_visible=True, rangeslider_thickness=0.04)
        fig.update_yaxes(showgrid=True, gridcolor='#363a45', side='right')

        return fig

    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
        """HEX颜色转RGBA字符串"""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return f'rgba({r}, {g}, {b}, {alpha})'
