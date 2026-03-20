"""数据加载器"""
import pandas as pd


def load_indicator(filepath: str) -> pd.DataFrame:
    """统一的数据加载接口

    Args:
        filepath: 指标文件路径，支持 .pkl 和 .csv 格式

    Returns:
        DataFrame，index 名为 'date'
    """
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
