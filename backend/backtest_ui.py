
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from backtest_engine import BacktestEngine
import akshare as ak

# --- Page Config ---
st.set_page_config(
    page_title="量化回测平台",
    page_icon="🔬",
    layout="wide"
)

# --- Styling ---
# Inject custom CSS for the "High-end Blue-White Lab Style"
st.markdown("""
<style>
    /* Main background and text */
    .stApp {
        background-color: #F8F9FA;
    }
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }
    /* Metric cards */
    .st-emotion-cache-1gulkj5 {
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 20px;
        background-color: #FFFFFF;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    /* Metric labels */
    .st-emotion-cache-1gulkj5 .st-emotion-cache-16idsys p {
        font-size: 16px;
        color: #6B7280; /* Gray-500 */
    }
    /* Metric values */
    .st-emotion-cache-1gulkj5 .st-emotion-cache-1ht1j8p {
        font-size: 28px;
        font-weight: 600;
        color: #1E5ED2; /* Investment Blue */
    }
    /* Positive metric values */
    .positive-metric {
        color: #059669 !important; /* Mint Green */
    }
    /* Negative metric values */
    .negative-metric {
        color: #F6353F !important; /* Coral Red */
    }
    /* Plotly chart background */
    .plot-container {
        background-color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)


# --- Sidebar ---
st.sidebar.header("参数配置")

# --- Symbol and Market Selection ---
st.sidebar.subheader("标的配置")
market = st.sidebar.radio(
    '选择市场',
    ('A股', '港股', '美股'),
    horizontal=True,
)

# Helper to construct yfinance-compatible symbol
def get_yfinance_symbol(market, code):
    if not code:
        return None
    if market == 'A股':
        # Simple check for Shanghai vs Shenzhen
        return f"{code}.SS" if code.startswith('6') else f"{code}.SZ"
    elif market == '港股':
        # Pad with zeros to 4 digits for many HK stocks
        return f"{code.zfill(4)}.HK"
    elif market == '美股':
        return code.upper()
    return code

symbol_input = st.sidebar.text_input('输入代码 (例如: 600519, 0700, AAPL)', '600519')
symbol = get_yfinance_symbol(market, symbol_input)

# --- Date and Capital ---
start_date = st.sidebar.date_input('开始日期', pd.to_datetime('2021-01-01'))
end_date = st.sidebar.date_input('结束日期', pd.to_datetime('2023-12-31'))
initial_capital = st.sidebar.number_input('初始资金', min_value=1000, value=50000, step=1000)

# --- Benchmark Selection ---
st.sidebar.subheader("基准配置")
benchmark_symbol = st.sidebar.selectbox(
    '选择基准指数',
    options=['sh000300', 'sh000905', '^GSPC', '^IXIC'],
    format_func=lambda x: {
        'sh000300': '沪深300',
        'sh000905': '中证1000',
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ'
    }.get(x, x)
)

# --- Strategy and Execution ---
st.sidebar.subheader("策略配置")
nl_strategy = st.sidebar.text_area(
    '自然语言策略',
    '收盘价站上20日均线买入，跌破卖出',
    height=100
)

run_button = st.sidebar.button("🚀 运行回测")

# --- Main Content ---
st.title("🔬 量化回测平台")

if run_button:
    with st.spinner('正在运行回测，请稍候...'):
        try:
            # Initialize and run backtest
            engine = BacktestEngine(
                symbol=symbol,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                initial_capital=initial_capital
            )
            strategy_func = engine.parse_strategy_from_natural_language(nl_strategy)
            results_df, metrics = engine.run_backtest(strategy_func, benchmark_symbol=benchmark_symbol)

            # --- Metrics Dashboard ---
            st.subheader("核心指标看板")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    label="年化收益率",
                    value=f"{metrics['annualized_return']:.2%}",
                    delta_color="off"
                )
            with col2:
                st.metric(
                    label="最大回撤",
                    value=f"{metrics['max_drawdown']:.2%}",
                )
                st.markdown(f'<p class="negative-metric">{metrics["max_drawdown"]:.2%}</p>', unsafe_allow_html=True)

            with col3:
                st.metric(
                    label="夏普比率",
                    value=f"{metrics['sharpe_ratio']:.2f}"
                )
            with col4:
                st.metric(
                    label="胜率",
                    value=f"{metrics['win_rate']:.2%}"
                )


            # --- Net Value Curve ---
            st.subheader("净值曲线")
            fig = go.Figure()

            # Add Portfolio Value trace
            fig.add_trace(go.Scatter(
                x=results_df.index,
                y=results_df['portfolio_value'],
                mode='lines',
                name='策略净值',
                line=dict(color='#1E5ED2', width=2) # Investment Blue
            ))

            # Add Benchmark trace
            fig.add_trace(go.Scatter(
                x=results_df.index,
                y=results_df['benchmark_value'],
                mode='lines',
                name='基准净值',
                line=dict(color='#D1D5DB', width=2, dash='dash') # Light Gray
            ))

            fig.update_layout(
                margin=dict(l=0, r=0, t=40, b=0),
                paper_bgcolor='#FFFFFF',
                plot_bgcolor='#FFFFFF',
                xaxis_title='日期',
                yaxis_title='净值',
                legend=dict(x=0.01, y=0.98)
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- AI Attribution Report ---
            st.subheader("AI 归因分析报告")
            with st.expander("点击查看AI生成的详细分析", expanded=True):
                report = engine.mock_llm_attribution_report(metrics, nl_strategy)
                st.markdown(report, unsafe_allow_html=True)

            # --- Save to Feishu ---
            if st.button("💾 保存到飞书"):
                with st.spinner('正在保存结果到飞书...'):
                    engine.save_results_to_feishu(metrics, nl_strategy)
                    st.success("回测结果已成功保存到飞书!")

        except Exception as e:
            st.error(f"回测过程中发生错误: {e}")

else:
    st.info("请在左侧配置参数并运行回测。")

