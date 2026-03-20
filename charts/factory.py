"""图表工厂"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Tuple, Optional

from config import get_ticker_color, get_ticker_name


class ChartFactory:
    """统一管理 Plotly 图表创建"""

    DEFAULT_COLORS = ['#00b8a9', '#f75b5b', '#f7cc35', '#4caf50', '#9c27b0', '#2196f3']

    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
        """HEX颜色转RGBA字符串"""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return f'rgba({r}, {g}, {b}, {alpha})'

    def create_line_chart(
        self,
        title: str,
        traces_data: List[Tuple[str, pd.Series, str, Optional[float]]],
        subplot_titles: Optional[List[str]] = None
    ) -> go.Figure:
        """创建标准线图

        Args:
            title: 图表标题
            traces_data: [(name, series, color, width), ...]
            subplot_titles: 子图标题列表

        Returns:
            Plotly Figure 对象
        """
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
                        shape='spline',
                    ),
                    fill='tozeroy' if idx == 1 else None,
                    fillcolor=self._hex_to_rgba(color, 0.1) if idx == 1 else None,
                ),
                row=idx, col=1
            )

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

        fig.update_xaxes(rangeslider_visible=True, rangeslider_thickness=0.04, row=rows, col=1)

        return fig

    def create_bar_chart(
        self,
        title: str,
        traces_data: List[Tuple[str, pd.Series, str]]
    ) -> go.Figure:
        """创建柱状图

        Args:
            title: 图表标题
            traces_data: [(name, series, color), ...]

        Returns:
            Plotly Figure 对象
        """
        fig = make_subplots(rows=1, cols=1)

        for trace_name, trace_y, color in traces_data:
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

    def create_comparison_line(
        self,
        indicators: List[dict],
        title: Optional[str] = None
    ) -> Optional[go.Figure]:
        """创建多标的线图对比

        Args:
            indicators: 指标列表，每个包含 filepath, ticker, window 等
            title: 图表标题

        Returns:
            Plotly Figure 或 None
        """
        from data import load_indicator

        traces_data = []
        colors = list(self.DEFAULT_COLORS)

        for idx, ind in enumerate(indicators):
            df = load_indicator(ind['filepath'])
            if df is None:
                continue
            col_name = df.columns[0]
            color = get_ticker_color(ind['ticker']) or colors[idx % len(colors)]
            name = get_ticker_name(ind['ticker'])
            if ind.get('window'):
                name += f" {ind['window']}日"
            traces_data.append((name, df[col_name], color, 2))

        if not traces_data:
            return None

        chart_title = title or (indicators[0]['name'] if indicators else '对比')
        return self.create_line_chart(title=chart_title, traces_data=traces_data)

    def create_comparison_bar(
        self,
        indicators: List[dict],
        title: Optional[str] = None
    ) -> Optional[go.Figure]:
        """创建多标的柱状对比

        Args:
            indicators: 指标列表
            title: 图表标题

        Returns:
            Plotly Figure 或 None
        """
        from data import load_indicator

        traces_data = []
        colors = list(self.DEFAULT_COLORS)

        for idx, ind in enumerate(indicators):
            df = load_indicator(ind['filepath'])
            if df is None:
                continue
            col_name = df.columns[0]
            color = get_ticker_color(ind['ticker']) or colors[idx % len(colors)]
            name = get_ticker_name(ind['ticker'])
            if ind.get('window'):
                name += f" {ind['window']}日"
            traces_data.append((name, df[col_name], color))

        if not traces_data:
            return None

        chart_title = title or (indicators[0]['name'] if indicators else '对比')
        return self.create_bar_chart(title=chart_title, traces_data=traces_data)
