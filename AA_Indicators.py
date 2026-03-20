"""
量化大类资产指标研究框架 V1.0
--------------------------------------------------
设计理念：数据与计算解耦，指标单文件存储，便于多人协同与多因子回测。
当前模块：数据引擎底座 & 量价类指标集
"""

import pandas as pd
import numpy as np
import os
from typing import List

# ==========================================
# 模块一：统一数据引擎 (DataLoader)
# 负责底层数据的抓取、清洗与标准化
# ==========================================
class DataLoader:
    def __init__(self, root_dir: str):
        """
        初始化数据引擎
        :param root_dir: 团队共享的数据根目录
        """
        self.root_dir = root_dir
        
        # MAC数据路由表：统一定义各类数据的存放路径 (方便未来按需扩展)
        self.source_map = {
            "量价": r"原始数据/指数量价数据-日度更新",
            "宏观": r"原始数据/宏观经济数据",
            "估值": r"原始数据/指数估值数据"
        }


        # WIN数据路由表：统一定义各类数据的存放路径 (方便未来按需扩展)
        self.source_map = {
            "量价": r"E:\择时模型数据\指数量价数据-非日度更新",
            "宏观": r"原始数据\宏观经济数据",
            "估值": r"原始数据\指数估值数据"
        }


    def fetch(self, ticker: str, category: str = "量价") -> pd.DataFrame:
        """
        核心数据获取接口
        :param ticker: 资产代码，例如 "000300.SH"
        :param category: 数据类别，默认 "量价"
        :return: 标准化处理后的 DataFrame (日期为Index，列名为小写)
        """
        sub_dir = self.source_map.get(category)
        if not sub_dir:
            raise ValueError(f"引擎错误：未知的数据类别 '{category}'，请在 DataLoader 中配置。")
            
        file_path = os.path.join(self.root_dir, sub_dir, f"{ticker}.csv")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"引擎错误：找不到数据文件 {file_path}")

        # 1. 鲁棒性读取（兼容逗号、制表符、BOM隐藏字符等各类脏格式）
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8-sig')
        except Exception:
            df = pd.read_csv(file_path, delim_whitespace=True, encoding='utf-8-sig')

        # 2. 字段清洗：列名统一转小写并去除空格
        df.columns = df.columns.str.strip().str.lower()

        # 3. 时间序列标准化：强制转换为日期索引并按升序排列
        # 兼容 date 或 time 作为日期列名
        date_col = 'date' if 'date' in df.columns else 'time'
        df[date_col] = pd.to_datetime(df[date_col])
        df.set_index(date_col, inplace=True)
        df.sort_index(ascending=True, inplace=True)
        
        return df


# ==========================================
# 模块二：量价类指标计算库 (面向研究员协同编写)
# 职责：调用数据引擎获取数据，进行指标公式计算，并通过内部方法统一输出
# ==========================================
class VolumePriceIndicators:
    def __init__(self, data_loader: DataLoader, output_dir: str):
        """
        初始化量价类指标模块
        :param data_loader: 实例化后的 DataLoader 数据引擎
        :param output_dir: 指标计算结果的保存目录
        """
        self.loader = data_loader
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True) # 如果目录不存在则自动创建

    def _save_result(self, result_df: pd.DataFrame, file_name: str):
        """
        [内部辅助方法]：统一负责结果的清洗与落盘
        研究员在编写具体指标时，只需调用此方法即可，无需关心文件 IO 逻辑。
        """
        # 自动去除因计算移动平均/收益率产生的初始空值 (NaN)
        result_df.dropna(inplace=True)

        # 输出为pkl格式（更轻量，Python原生支持）
        pkl_name = file_name.replace('.csv', '.pkl')
        save_path = os.path.join(self.output_dir, pkl_name)
        result_df.to_pickle(save_path)
        print(f"  成功生成: {pkl_name}")

    # ---------------- 基础/跨品种指标区 ----------------
    
    def calc_and_save_amt(self, ticker: str):
        """计算单品种成交额"""
        df = self.loader.fetch(ticker, category="量价")
        ind_df = df[['amt']].rename(columns={'amt': f'{ticker}_成交额'})
        self._save_result(ind_df, f"{ticker}_amt.csv")
    
    def calc_and_save_amt_ratio(self, ticker: str, market_ticker: str = "930709.CSI"):
        """
        计算个股/指数成交额占全市场的百分比
        :param ticker: 目标资产代码
        :param market_ticker: 万得全A指数的代码 (请确保文件名与此处一致)
        """
        df = self.loader.fetch(ticker, category="量价")
        df_market = self.loader.fetch(market_ticker, category="量价")
        ratio = (df['amt'] / df_market['amt'] * 100).to_frame(name=f'{ticker}_占市场比重')
        self._save_result(ratio, f"{ticker}_vs_market_amt_ratio.csv")

    def calc_relative_strength(self, ticker_a: str, ticker_b: str):
        """计算相对强弱比值 (揭示风格切换的经典择时因子)"""
        df_a = self.loader.fetch(ticker_a, category="量价")
        df_b = self.loader.fetch(ticker_b, category="量价")
        
        # Pandas 会自动按日期对齐，避免停牌导致的数据错位
        ratio = (df_a['close'] / df_b['close']).to_frame(name=f'{ticker_a}_对_{ticker_b}_相对强弱')
        self._save_result(ratio, f"{ticker_a}_vs_{ticker_b}_rs.csv")

    def calc_relative_turnover(self, ticker_a: str, ticker_b: str):
        """计算相对换手率比值 (揭示市场资金偏好切换)"""
        df_a = self.loader.fetch(ticker_a, category="量价")
        df_b = self.loader.fetch(ticker_b, category="量价")
        
        if 'free_turn' not in df_a.columns or 'free_turn' not in df_b.columns:
            print(f"  ⚠️ 警告: {ticker_a} 或 {ticker_b} 数据缺失 'free_turn' 列，跳过计算。")
            return

        ratio = (df_a['free_turn'] / df_b['free_turn']).to_frame(name=f'{ticker_a}_对_{ticker_b}_相对换手率')
        self._save_result(ratio, f"{ticker_a}_vs_{ticker_b}_rt.csv")

        
    # ---------------- 动量与趋势指标区 ----------------
    
    def calc_and_save_pchg_abs(self, ticker: str, n: int = 1):
        """
        计算标的 N日涨跌幅绝对值 (PCHG_ABS)
        反映标的价格波动的绝对幅度。公式：ABS((CLOSE / CLOSE(N) - 1) * 100)
        """
        df = self.loader.fetch(ticker, category="量价")
        pchg_abs = (df['close'].pct_change(n).abs() * 100).to_frame(name=f'{ticker}_涨跌幅绝对值_{n}日')
        self._save_result(pchg_abs, f"{ticker}_pchg_abs_{n}d.csv")

    def calc_and_save_mom(self, ticker: str, windows: List[int] = [20, 60, 120]):
        """
        计算标的多日动量 (MOM)
        衡量标的短/中/长期价格趋势强度。公式：(CLOSE / CLOSE(N) - 1) * 100
        """
        df = self.loader.fetch(ticker, category="量价")
        for n in windows:
            mom = (df['close'].pct_change(n) * 100).to_frame(name=f'{ticker}_动量_{n}日')
            self._save_result(mom, f"{ticker}_mom_{n}d.csv")

    def calc_and_save_ma(self, ticker: str, windows: List[int] = [20, 60, 120]):
        """
        计算标的移动均线 (MA)
        衡量标的短/中/长期价格均线水平。公式：MA(CLOSE, N)
        """
        df = self.loader.fetch(ticker, category="量价")
        for n in windows:
            ma = df['close'].rolling(window=n).mean().to_frame(name=f'{ticker}_均线_{n}日')
            self._save_result(ma, f"{ticker}_ma_{n}d.csv")

    def calc_and_save_ma_turnover(self, ticker: str, windows: List[int] = [20, 60, 120]):
        """计算移动平均换手率 (需确保数据源中有 'free_turn' 列)"""
        df = self.loader.fetch(ticker, category="量价")
        if 'free_turn' not in df.columns:
            print(f"  ⚠️ 警告: 数据中缺失 'turnover' 列，无法计算换手率。")
            return
            
        for n in windows:
            ma_turnover = df['free_turn'].rolling(window=n).mean().to_frame(name=f'{ticker}_换手率均值_{n}日')
            self._save_result(ma_turnover, f"{ticker}_ma_turnover_{n}d.csv")

    def calc_and_save_ma_deviation(self, ticker: str, windows: List[int] = [20, 60, 120]):
        """计算均线偏离度: (CLOSE - MA) / MA * 100"""
        df = self.loader.fetch(ticker, category="量价")
        for n in windows:
            ma = df['close'].rolling(window=n).mean()
            deviation = ((df['close'] - ma) / ma * 100).to_frame(name=f'{ticker}_偏离度_{n}日')
            self._save_result(deviation, f"{ticker}_ma_dev_{n}d.csv")

    def calc_and_save_rsi_percentile(self, ticker: str, rsi_win: int = 14, p_win: int = 120):
        """计算 RSI 及 30%/70% 分位值"""
        df = self.loader.fetch(ticker, category="量价")
        delta = df['close'].diff()
        
        # 获取上涨部分和下跌部分
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        # 计算 RSI
        avg_gain = gain.rolling(window=rsi_win).mean()
        avg_loss = loss.rolling(window=rsi_win).mean()
        rsi = (avg_gain / (avg_gain + avg_loss)) * 100
        
        # 计算分位值 (Rolling Percentile)
        rsi_30p = rsi.rolling(window=p_win).quantile(0.3)
        rsi_70p = rsi.rolling(window=p_win).quantile(0.7)
        
        result = pd.DataFrame({
            f'{ticker}_RSI': rsi,
            f'{ticker}_RSI_30P': rsi_30p,
            f'{ticker}_RSI_70P': rsi_70p
        })
        self._save_result(result, f"{ticker}_rsi_analysis.csv")

    def calc_and_save_volatility(self, ticker: str, windows: List[int] = [20, 60, 120]):
        """
        计算滚动年化波动率 (Volatility)
        反映标的价格波动的激烈程度。
        公式：Std(Log_Return, N) * sqrt(242) * 100
        :param windows: 滚动计算窗口，例如 20日(月)、60日(季)
        """
        # 1. 获取量价数据
        df = self.loader.fetch(ticker, category="量价")
        
        # 2. 计算对数收益率 (Log Return): ln(P_t / P_{t-1})
        # 对数收益率在数学处理上比简单收益率更具对称性和可加性
        log_ret = np.log(df['close'] / df['close'].shift(1))
        
        for n in windows:
            # 3. 计算滚动标准差并进行年化处理
            # 242 为 A 股一年平均交易日，sqrt(242) 是将日频波动率转化为年频的标准系数
            vol = (log_ret.rolling(window=n).std() * np.sqrt(242) * 100).to_frame(name=f'{ticker}_年化波动率_{n}日')
            
            # 4. 统一落盘
            self._save_result(vol, f"{ticker}_vol_{n}d.csv")
# ==================================================
# 实际运行脚本 (支持配置化与批量执行)
# ==================================================
if __name__ == "__main__":
    # --- 1. 系统路径配置 ---
    ROOT_PATH = r"E:\择时模型数据\指数量价数据-非日度更新"
    OUTPUT_PATH = r"e:\AA-model\指标结果库"
    
    """！！！在这里加标的！！！"""
    TARGET_ASSETS = ["000300.SH", "000905.SH", "000852.SH", "932000.CSI", "8841431.WI", "881001.WI"]
    
    print("="*50)
    print("启动投研指标批量生产任务")
    print("="*50)

    # --- 2. 挂载引擎与模块 ---
    loader = DataLoader(root_dir=ROOT_PATH)
    vp_module = VolumePriceIndicators(data_loader=loader, output_dir=OUTPUT_PATH)
    
    # --- 3. 执行任务队列 ---
    for ticker in TARGET_ASSETS:
        print(f"\n正在处理资产标的: [ {ticker} ]")
        
        # 执行指标计算 (参数化控制生成周期)
        vp_module.calc_and_save_amt(ticker)
        vp_module.calc_and_save_amt_ratio(ticker)
        vp_module.calc_and_save_pchg_abs(ticker, n=1)
        vp_module.calc_and_save_mom(ticker, windows=[20, 60, 120])
        vp_module.calc_and_save_ma(ticker, windows=[20, 60, 120])
        vp_module.calc_and_save_ma_turnover(ticker)
        vp_module.calc_and_save_ma_deviation(ticker)
        vp_module.calc_and_save_rsi_percentile(ticker)
        vp_module.calc_and_save_volatility(ticker, windows=[20, 60, 120])
        
    print("\n正在处理跨品种指标...")
    vp_module.calc_relative_strength(ticker_a="000300.SH", ticker_b="000905.SH")
    vp_module.calc_relative_strength(ticker_a="000300.SH", ticker_b="000852.SH")
    vp_module.calc_relative_strength(ticker_a="000300.SH", ticker_b="932000.CSI")
    vp_module.calc_relative_strength(ticker_a="000300.SH", ticker_b="8841431.WI")
    vp_module.calc_relative_strength(ticker_a="000905.SH", ticker_b="000852.SH")
    vp_module.calc_relative_strength(ticker_a="000905.SH", ticker_b="932000.CSI")
    vp_module.calc_relative_strength(ticker_a="000905.SH", ticker_b="8841431.WI")
    vp_module.calc_relative_strength(ticker_a="000852.SH", ticker_b="8841431.WI")


    vp_module.calc_relative_turnover(ticker_a="000300.SH", ticker_b="000905.SH")
    vp_module.calc_relative_turnover(ticker_a="000300.SH", ticker_b="000852.SH")
    vp_module.calc_relative_turnover(ticker_a="000300.SH", ticker_b="932000.CSI")
    vp_module.calc_relative_turnover(ticker_a="000300.SH", ticker_b="8841431.WI")
    vp_module.calc_relative_turnover(ticker_a="000905.SH", ticker_b="000852.SH")
    vp_module.calc_relative_turnover(ticker_a="000905.SH", ticker_b="932000.CSI")
    vp_module.calc_relative_turnover(ticker_a="000905.SH", ticker_b="8841431.WI")
    vp_module.calc_relative_turnover(ticker_a="000852.SH", ticker_b="8841431.WI")  
      

    print("\n[OK] 任务结束：所有核心技术指标已成功生成并分类入库！")
    print("="*50)