"""
量化大类资产指标研究框架 V1.0
--------------------------------------------------
设计理念：数据与计算解耦，指标单文件存储，便于多人协同与多因子回测。
当前模块：数据引擎底座 & 量价类指标集
"""

import pandas as pd
import numpy as np
import os
from typing import List, Optional

# ==========================================
# 模块一：统一数据引擎 (DataLoader)
# 负责底层数据的抓取、清洗与标准化
# ==========================================

# A股年平均交易日
TRADING_DAYS_PER_YEAR = 242


class DataLoader:
    def __init__(self, root_dir: str):
        """
        初始化数据引擎
        :param root_dir: 团队共享的数据根目录
        """
        self.root_dir = root_dir

        # 数据路由表：根据操作系统自动选择路径
        import platform
        system = platform.system()
        
        
        if system == "Windows":
            self.source_map = {
                "量价": r"E:\数据库\ETF跟踪指数量价数据-日度更新\ETF跟踪指数量价数据-日度更新",
                "宏观": r"原始数据\宏观经济数据",
                "估值": r"原始数据\宏观与基本面数据-日度更新"
            }
        else:  # Mac / Linux
            self.source_map = {
                "量价": r"原始数据/指数量价数据-日度更新",
                "宏观": r"原始数据/宏观经济数据",
                "估值": r"原始数据/宏观与基本面数据-日度更新"
            }
        


    def fetch(self, ticker: str, category: str = "量价", filename: Optional[str] = None) -> pd.DataFrame:
        """
        核心数据获取接口
        :param ticker: 资产代码，例如 "000300.SH"
        :param category: 数据类别，默认 "量价"
        :param filename: 可选文件名（含后缀），默认使用 "{ticker}.csv"
        :return: 标准化处理后的 DataFrame (日期为Index，列名为小写)
        """
        sub_dir = self.source_map.get(category)
        if not sub_dir:
            raise ValueError(f"引擎错误：未知的数据类别 '{category}'，请在 DataLoader 中配置。")
            
        target_filename = filename or f"{ticker}.csv"
        file_path = os.path.join(self.root_dir, sub_dir, target_filename)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"引擎错误：找不到数据文件 {file_path}")

        # 1. 鲁棒性读取（兼容 CSV / Excel 与常见脏格式）
        file_path_lower = file_path.lower()
        if file_path_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)
        else:
            try:
                df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8-sig')
            except Exception:
                df = pd.read_csv(file_path, delim_whitespace=True, encoding='utf-8-sig')

        # 2. 字段清洗：列名统一转小写并去除空格
        df.columns = df.columns.str.strip().str.lower()

        # 3. 时间序列标准化：强制转换为日期索引并按升序排列
        # 兼容 date / time / datetime
        if 'date' in df.columns:
            date_col = 'date'
        elif 'time' in df.columns:
            date_col = 'time'
        elif 'datetime' in df.columns:
            date_col = 'datetime'
        else:
            raise ValueError(f"引擎错误：{target_filename} 缺失 date/time/datetime 列。")
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
        result_df = result_df.dropna()

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
        计算成交额占全市场的对数占比 (Log Amount Ratio)
        公式：log(ticker_amt / market_amt)
        """
        df = self.loader.fetch(ticker, category="量价")
        df_market = self.loader.fetch(market_ticker, category="量价")
        
        # 使用 log 避免成交额绝对值差距过大，反映相对活跃度的变动
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = np.log(df['amt'] / df_market['amt']).to_frame(name=f'{ticker}_成交额对数占比')
            
        self._save_result(ratio, f"{ticker}_vs_market_amt_ratio.csv")

    def calc_relative_strength(self, ticker_a: str, ticker_b: str):
        """
        计算对数相对强弱 (Log Relative Strength)
        公式：log(price_a / price_b)
        """
        df_a = self.loader.fetch(ticker_a, category="量价")
        df_b = self.loader.fetch(ticker_b, category="量价")

        # 对数化处理：log(A/B) 等同于 log(A) - log(B)
        # 这能将比率转化为围绕 0 轴波动的序列
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = np.log(df_a['close'] / df_b['close']).to_frame(name=f'{ticker_a}_对_{ticker_b}_对数相对强弱')

        self._save_result(ratio, f"{ticker_a}_vs_{ticker_b}_rs.csv")

    def calc_relative_turnover(self, ticker_a: str, ticker_b: str):
        """
        计算对数相对换手率 (Log Relative Turnover)
        公式：log(turnover_a / turnover_b)
        """
        df_a = self.loader.fetch(ticker_a, category="量价")
        df_b = self.loader.fetch(ticker_b, category="量价")
        
        if 'free_turn' not in df_a.columns or 'free_turn' not in df_b.columns:
            print(f"  ⚠️ 警告: {ticker_a} 或 {ticker_b} 缺失换手率数据。")
            return

        with np.errstate(divide='ignore', invalid='ignore'):
            # 换手率分布通常极度右偏，log 处理后更适合用于回归或机器学习模型
            ratio = np.log(df_a['free_turn'] / df_b['free_turn']).to_frame(name=f'{ticker_a}_对_{ticker_b}_对数相对换手率')

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

    def calc_and_save_high_new(self, ticker: str, windows: List[int] = [90, 250, 750]):
        """
        是否新高：当日收盘价是否等于近 N 日收盘价最大值。
        公式：HIGH_NEW(N) = IF(CLOSE = MAX(CLOSE, N), 1, 0)
        默认 N=90/250/750，约对应 3 个月 / 1 年 / 3 年交易日。
        """
        df = self.loader.fetch(ticker, category="量价")
        close = df["close"]
        for n in windows:
            roll_max = close.rolling(window=n, min_periods=n).max()
            # 窗口未满时不标记 0/1，避免与 roll_max 为 NaN 时误得 False
            high_new = (
                (close == roll_max).where(roll_max.notna()).astype(np.float64).to_frame(
                    name=f"{ticker}_是否新高_{n}日"
                )
            )
            self._save_result(high_new, f"{ticker}_high_new_{n}d.csv")

    def calc_and_save_low_new(self, ticker: str, windows: List[int] = [90, 250, 750]):
        """
        是否新低：当日收盘价是否等于近 N 日收盘价最小值。
        公式：LOW_NEW(N) = IF(CLOSE = MIN(CLOSE, N), 1, 0)
        默认 N=90/250/750，约对应 3 个月 / 1 年 / 3 年交易日。
        """
        df = self.loader.fetch(ticker, category="量价")
        close = df["close"]
        for n in windows:
            roll_min = close.rolling(window=n, min_periods=n).min()
            low_new = (
                (close == roll_min).where(roll_min.notna()).astype(np.float64).to_frame(
                    name=f"{ticker}_是否新低_{n}日"
                )
            )
            self._save_result(low_new, f"{ticker}_low_new_{n}d.csv")

    def calc_and_save_return_acf1(self, ticker: str, windows: List[int] = [20, 60, 120]):
        """
        趋势连续度：日收益率序列的一阶自相关系数 ACF(1)。
        公式：ACF_1 = AUTOCORRELATION(RETURN, 1)；在滚动窗口内对日简单收益率计算样本 lag-1 自相关。
        """
        df = self.loader.fetch(ticker, category="量价")
        ret = df["close"].pct_change()

        def _lag1_acf(x: pd.Series) -> float:
            s = x.dropna()
            if len(s) < 3:
                return np.nan
            v = s.autocorr(lag=1)
            return float(v) if v == v else np.nan

        for n in windows:
            acf1 = ret.rolling(window=n, min_periods=n).apply(
                _lag1_acf, raw=False
            ).to_frame(name=f"{ticker}_趋势连续度_{n}日")
            self._save_result(acf1, f"{ticker}_return_acf1_{n}d.csv")

    def calc_and_save_implied_vol(self, iv_ticker: str):
        """
        隐含波动率（IV）指标。

        说明：
        - Wind 的 IV 指数（如 SH_510050IV.WI）本身就是隐含波动率序列
        - 这里直接取其 close 作为 IV 值输出
        """
        df = self.loader.fetch(iv_ticker, category="量价")
        if "close" not in df.columns:
            print(f"  ⚠️ 警告: {iv_ticker} 缺失 close 列，无法生成 IV 指标。")
            return

        iv = pd.to_numeric(df["close"], errors="coerce").to_frame(name=f"{iv_ticker}_隐含波动率")
        self._save_result(iv, f"{iv_ticker}_iv.csv")

    def calc_and_save_margin(self):
        """
        两融余额（市场级）。
        数据源：M0075992_margin_balance.csv
        """
        try:
            df = self.loader.fetch(
                ticker="MARKET",
                category="估值",
                filename="M0075992_margin_balance.csv",
            )
        except FileNotFoundError:
            print("  ⚠️ 警告: 未找到两融余额数据文件（M0075992_margin_balance），跳过。")
            return

        if "close" in df.columns:
            series = pd.to_numeric(df["close"], errors="coerce")
        else:
            # 兜底：取第一个数值列
            numeric_df = df.apply(pd.to_numeric, errors="coerce")
            series = numeric_df.iloc[:, 0] if not numeric_df.empty else pd.Series(dtype=float)

        result = series.dropna().to_frame(name="MARKET_两融余额")
        self._save_result(result, "MARKET_margin.csv")

    def calc_and_save_north(self):
        """
        北向资金总成交额（市场级）。
        数据源：northbound_total_total_amount_cny_100m.csv
        """
        try:
            df = self.loader.fetch(
                ticker="MARKET",
                category="估值",
                filename="northbound_total_total_amount_cny_100m.csv",
            )
        except FileNotFoundError:
            print("  ⚠️ 警告: 未找到北向资金数据文件（northbound_total_total_amount_cny_100m），跳过。")
            return

        if "close" in df.columns:
            series = pd.to_numeric(df["close"], errors="coerce")
        else:
            numeric_df = df.apply(pd.to_numeric, errors="coerce")
            series = numeric_df.iloc[:, 0] if not numeric_df.empty else pd.Series(dtype=float)

        result = series.dropna().to_frame(name="MARKET_北向资金")
        self._save_result(result, "MARKET_north.csv")

    def calc_and_save_net_subscription(self, ticker: str):
        """
        净申购（按标的）。
        数据源：{ticker}_mfd_netbuyvol.csv
        """
        try:
            df = self.loader.fetch(
                ticker=ticker,
                category="估值",
                filename=f"{ticker}_mfd_netbuyvol.csv",
            )
        except FileNotFoundError:
            print(f"  ⚠️ 警告: 未找到 {ticker} 的净申购数据文件（mfd_netbuy_vol），跳过。")
            return

        if "close" in df.columns:
            series = pd.to_numeric(df["close"], errors="coerce")
        else:
            numeric_df = df.apply(pd.to_numeric, errors="coerce")
            series = numeric_df.iloc[:, 0] if not numeric_df.empty else pd.Series(dtype=float)

        result = series.dropna().to_frame(name=f"{ticker}_净申购")
        self._save_result(result, f"{ticker}_net_subscription.csv")

    def calc_and_save_erp(
        self,
        ticker: str,
        pe_field: str = "pe_ttm",
        pe_category: str = "估值",
        bond_ticker: str = "TB10Y.WI",
        bond_category: str = "量价",
    ):
        """
        股债风险溢价（ERP）:
        ERP = 1 / PE - 10年国债收益率

        口径统一：
        - PE 先转换为盈利收益率百分比点：100 / PE
        - 10Y 使用百分比点口径（例如 1.76）
        - ERP = 100 / PE - 10Y
        """
        pe_filename = f"{ticker}_{pe_field}.csv"
        try:
            pe_df = self.loader.fetch(ticker, category=pe_category, filename=pe_filename)
        except FileNotFoundError:
            print(f"  ⚠️ 警告: 未找到 {ticker} 的 PE 文件（{pe_filename}），类别: {pe_category}，跳过 ERP 计算。")
            return

        # 10年国债收益率默认从量价目录读取（TB10Y.WI）
        bond_df = self.loader.fetch(bond_ticker, category=bond_category)
        if "close" not in bond_df.columns:
            print(f"  ⚠️ 警告: {bond_ticker} 缺失 close 列，无法计算 ERP。")
            return

        pe_col = pe_field if pe_field in pe_df.columns else ("close" if "close" in pe_df.columns else None)
        if pe_col is None:
            print(f"  ⚠️ 警告: {pe_filename} 缺失 {pe_field}/close 列，跳过 ERP 计算。")
            return

        pe_series = pd.to_numeric(pe_df[pe_col], errors="coerce").dropna()
        if pe_series.empty:
            print(f"  ⚠️ 警告: {ticker} 的 PE 序列为空，跳过 ERP 计算。")
            return

        y10_series = pd.to_numeric(bond_df["close"], errors="coerce").dropna()

        merged_df = pd.concat(
            [
                pe_series.rename("pe_ttm"),
                y10_series.rename("y10"),
            ],
            axis=1,
            join="inner",
        ).dropna()

        if merged_df.empty:
            print(f"  ⚠️ 警告: {ticker} PE 与 {bond_ticker} 日期无重叠，跳过 ERP 计算。")
            return

        with np.errstate(divide="ignore", invalid="ignore"):
            erp = (100.0 / merged_df["pe_ttm"]) - merged_df["y10"]

        result = erp.to_frame(name=f"{ticker}_股债风险溢价")
        self._save_result(result, f"{ticker}_erp.csv")

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
        # 防止除零：当 avg_gain + avg_loss 为 0 时（即价格无波动），RSI 保持为 NaN
        # NaN 在金融分析中更合理，表示无法计算有意义的方向
        with np.errstate(divide='ignore', invalid='ignore'):
            rsi = avg_gain / (avg_gain + avg_loss) * 100
            rsi = pd.Series(rsi).where((avg_gain + avg_loss) != 0, np.nan)
        
        # 计算分位值 (Rolling Percentile)
        rsi_30p = rsi.rolling(window=p_win).quantile(0.3)
        rsi_70p = rsi.rolling(window=p_win).quantile(0.7)
        
        result = pd.DataFrame({
            f'{ticker}_RSI': rsi,
            f'{ticker}_RSI_30P': rsi_30p,
            f'{ticker}_RSI_70P': rsi_70p
        })
        self._save_result(result, f"{ticker}_rsi.csv")

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
            # TRADING_DAYS_PER_YEAR 为 A 股一年平均交易日（约242天）
            vol = (log_ret.rolling(window=n).std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100).to_frame(name=f'{ticker}_年化波动率_{n}日')
            
            # 4. 统一落盘
            self._save_result(vol, f"{ticker}_vol_{n}d.csv")
# ==================================================
# 实际运行脚本 (支持配置化与批量执行)
# ==================================================

if __name__ == "__main__":
    import platform
    # 获取脚本当前所在文件夹 (AA-model)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    if platform.system() == "Windows":
        ROOT_PATH = r"E:\数据库\ETF跟踪指数量价数据-日度更新\ETF跟踪指数量价数据-日度更新"
    else:
        # Mac系统：自动定位到“原始数据”所在的父目录（通常是桌面）
        ROOT_PATH = os.path.dirname(BASE_DIR)


    OUTPUT_PATH = os.path.join(BASE_DIR, "指标结果库")

    """！！！在这里加标的！！！"""
    TARGET_ASSETS = ["000300.SH", "000905.SH", "000852.SH", "932000.CSI", "8841431.WI", "881001.WI"]
    IV_ASSETS = ["SH_510050IV.WI", "SH_510300IV.WI", "SH_510500IV.WI", "CFE_000852IV.WI"]
    
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
        vp_module.calc_and_save_high_new(ticker)
        vp_module.calc_and_save_low_new(ticker)
        vp_module.calc_and_save_return_acf1(ticker, windows=[20, 60, 120])
        vp_module.calc_and_save_erp(ticker)

    print("\n正在处理隐含波动率（IV）指标...")
    for iv_ticker in IV_ASSETS:
        print(f"\n正在处理IV指数: [ {iv_ticker} ]")
        vp_module.calc_and_save_implied_vol(iv_ticker)

    print("\n正在处理市场级估值指标...")
    vp_module.calc_and_save_margin()
    vp_module.calc_and_save_north()

    print("\n正在处理净申购指标...")
    for ticker in TARGET_ASSETS:
        vp_module.calc_and_save_net_subscription(ticker)
        
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
