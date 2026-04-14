"""API路由"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from .models import IndicatorsResponse, TickersResponse, ChartData
from .service import ChartService


router = APIRouter(prefix='/api', tags=['api'])


@router.get('/indicators', response_model=IndicatorsResponse)
async def get_indicators():
    """获取所有指标列表"""
    try:
        indicators = ChartService.get_indicators()
        tickers = ChartService.get_tickers()
        return IndicatorsResponse(indicators=indicators, tickers=tickers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/tickers', response_model=TickersResponse)
async def get_tickers():
    """获取所有标的"""
    try:
        tickers = ChartService.get_tickers()
        return TickersResponse(tickers=tickers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/charts/{chart_id}', response_model=ChartData)
async def get_chart(chart_id: str, window: str = '1Y'):
    """获取指定图表的完整数据

    Args:
        chart_id: 图表ID
        window: 滚动窗口期 ('6M', '1Y', '3Y', '5Y', 'ALL')
    """
    # 验证窗口参数
    valid_windows = ['6M', '1Y', '3Y', '5Y', 'ALL']
    if window not in valid_windows:
        window = '1Y'

    try:
        chart_data = ChartService.get_chart_data(chart_id, rolling_window=window)
        if chart_data is None:
            raise HTTPException(status_code=404, detail=f'Chart {chart_id} not found')
        return ChartData(**chart_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
