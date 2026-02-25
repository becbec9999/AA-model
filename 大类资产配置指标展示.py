import pandas as pd
import plotly.graph_objects as go
import os

# 1. 读取我们后端引擎跑出来的指标
data_dir = r"E:\AA-model\指标结果库"

# 读取数据 (请确保路径和文件名正确)
df_close = pd.read_csv(os.path.join(data_dir, "000300.SH_amt.csv"), index_col=0, parse_dates=True)
df_ma20 = pd.read_csv(os.path.join(data_dir, "000300.SH_ma_20d.csv"), index_col=0, parse_dates=True)
df_ma60 = pd.read_csv(os.path.join(data_dir, "000300.SH_ma_60d.csv"), index_col=0, parse_dates=True)

# 2. 创建一张交互式大图
fig = go.Figure()

# 添加成交额柱状图 (注意这里改成了大写的 SH)
fig.add_trace(go.Bar(
    x=df_close.index, 
    y=df_close['000300.SH_成交额'], 
    name='成交额', 
    opacity=0.3, 
    yaxis='y2'
))

# 添加20日均线 (注意这里改成了大写的 SH)
fig.add_trace(go.Scatter(
    x=df_ma20.index, 
    y=df_ma20['000300.SH_均线_20日'], 
    name='MA20', 
    line=dict(color='orange')
))

# 添加60日均线 (注意这里改成了大写的 SH)
fig.add_trace(go.Scatter(
    x=df_ma60.index, 
    y=df_ma60['000300.SH_均线_60日'], 
    name='MA60', 
    line=dict(color='blue')
))

# 3. 设置图表排版（双Y轴，带标题）
fig.update_layout(
    title='沪深300：量价与均线系统跟踪报告',
    xaxis_title='日期',
    yaxis=dict(title='指数点位'),
    yaxis2=dict(title='成交额', overlaying='y', side='right', showgrid=False),
    hovermode='x unified' # 鼠标悬停时显示一条贯穿上下的竖线和所有数据
)

# 4. 一键导出为脱机的 HTML 文件
output_html = "每日量价跟踪报告.html"
fig.write_html(output_html)
print(f"✅ 交互式报告已生成：{output_html}，直接双击用浏览器打开即可！")