"""API 数据模型"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class TickerInfo(BaseModel):
    """标的信息"""
    code: str
    name: str
    color: str


class IndicatorInfo(BaseModel):
    """指标信息"""
    id: str
    name: str
    pattern: str
    ticker: str
    category: str
    type: str
    window: Optional[int] = None
    is_cross: bool = False


class ChartData(BaseModel):
    """图表数据"""
    id: str
    title: str
    data: List[Dict[str, Any]]
    layout: Dict[str, Any]


class IndicatorsResponse(BaseModel):
    """指标列表响应"""
    indicators: Dict[str, Dict[str, List[IndicatorInfo]]]
    tickers: List[TickerInfo]


class TickersResponse(BaseModel):
    """标的列表响应"""
    tickers: List[TickerInfo]
