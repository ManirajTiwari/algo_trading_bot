import streamlit as st
import pandas as pd
from analyzer import search_ticker_symbol, get_single_summary, analyze_ticker
from visualizer import create_stock_chart

def setup_page():
    st.set_page_config(
        page_title="Algo Trading Dashboard",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
        <style>
        .main { background-color: #0e1117; }
        div[data-testid="stMetric"] {
            background-color: #1e222d;
            border: 1px solid #2a2e39;
            padding: 12px 16px;
            border-radius: 8px;
        }
        div[data-testid="stMetric"] label {
            color: #787b86 !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
        }
        div[data-testid="stMetricValue"] {
            color: #d1d4dc !important;
            font-size: 1.3rem !important;
            font-weight: 700 !important;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #2a2e39;
            border-radius: 8px;
        }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        </style>
    """, unsafe_allow_html=True)

def render_dashboard():
    # --- SIDEBAR CONTROL PANEL ---
    with st.sidebar:
        st.title("⚡ Control Panel")
        st.caption("Engine Parameters & Search")

        st.markdown("---")
        st.subheader("🔍 Asset Search")
        
        # Free-form search input box
        user_query = st.text_input(
            "Enter Ticker / Symbol:",
            value="RELIANCE.NS",
            help="NSE Indian stocks need '.NS' suffix (e.g., RELIANCE.NS, TATAMOTORS.NS). US stocks use raw ticker (e.g., AAPL, NVDA, TSLA)."
        )
        selected_symbol = search_ticker_symbol(user_query)

        st.markdown("---")
        st.subheader("⏱️ Timeframe & Data")
        selected_period = st.selectbox(
            "Select Duration:",
            options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=3
        )

        st.markdown("---")
        st.subheader("🛠️ Indicator Selection")
        selected_indicators = st.multiselect(
            "Choose indicators to analyze:",
            options=[
                "SMA 20 & 50",
                "RSI (14)",
                "MACD",
                "Bollinger Bands",
                "Volume Bars",
                "VWAP",
                "Supertrend"
            ],
            default=["SMA 20 & 50", "RSI (14)", "MACD", "Volume Bars"]
        )

        st.markdown("---")
        if st.button("🔄 Force Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # --- MAIN CONTENT AREA ---
    st.title("⚡ Algorithmic Trading Analytics Engine")
    st.caption(f"Real-time Analysis for Ticker: **{selected_symbol}**")

    # SECTION 1: SEARCH SUMMARY MATRIX
    st.subheader(f"📋 Live Signal Matrix ({selected_symbol})")
    with st.spinner(f"Fetching market data for {selected_symbol}..."):
        summary_df = get_single_summary(symbol=selected_symbol, period=selected_period, indicators=selected_indicators)

        if not summary_df.empty:
            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.error(f"Could not retrieve market data for symbol '{selected_symbol}'. Check ticker syntax (e.g. use .NS for Indian stocks).")

    st.markdown("---")

    # SECTION 2: DEEP DIVE & CHARTING
    if not summary_df.empty:
        st.subheader(f"🔍 Deep Dive Signal Breakdown: {selected_symbol}")

        df_selected = analyze_ticker(selected_symbol, period=selected_period, indicators=selected_indicators)

        if df_selected is not None and not df_selected.empty:
            latest = df_selected.iloc[-1]

            # Dynamic Indicator Signal Metric Cards
            st.markdown("#### **Active Indicator Signals**")
            metric_cols = st.columns(len(selected_indicators) + 1)

            metric_cols[0].metric("Last Price", f"{latest['Close']:.2f}")

            col_idx = 1
            if "SMA 20 & 50" in selected_indicators and pd.notna(latest['SMA_20']):
                sma_sig = "BUY 🟢" if latest['SMA_20'] > latest['SMA_50'] else "SELL 🔴"
                metric_cols[col_idx].metric("SMA (20/50)", f"{latest['SMA_20']:.1f}/{latest['SMA_50']:.1f}", delta=sma_sig, delta_color="normal" if "BUY" in sma_sig else "inverse")
                col_idx += 1

            if "RSI (14)" in selected_indicators and pd.notna(latest['RSI']):
                rsi_val = latest['RSI']
                rsi_sig = "SELL 🔴" if rsi_val > 70 else ("BUY 🟢" if rsi_val < 30 else "HOLD 🟡")
                metric_cols[col_idx].metric("RSI (14)", f"{rsi_val:.2f}", delta=rsi_sig, delta_color="off" if "HOLD" in rsi_sig else ("normal" if "BUY" in rsi_sig else "inverse"))
                col_idx += 1

            if "MACD" in selected_indicators and 'MACD' in latest and pd.notna(latest['MACD']):
                macd_sig = "BUY 🟢" if latest['MACD'] > latest['MACD_Signal'] else "SELL 🔴"
                metric_cols[col_idx].metric("MACD", f"{latest['MACD']:.2f}", delta=macd_sig, delta_color="normal" if "BUY" in macd_sig else "inverse")
                col_idx += 1

            if "Bollinger Bands" in selected_indicators and 'BB_Upper' in latest and pd.notna(latest['BB_Upper']):
                bb_sig = "SELL 🔴" if latest['Close'] >= latest['BB_Upper'] else ("BUY 🟢" if latest['Close'] <= latest['BB_Lower'] else "HOLD 🟡")
                metric_cols[col_idx].metric("Bollinger", f"{latest['Close']:.2f}", delta=bb_sig, delta_color="off" if "HOLD" in bb_sig else ("normal" if "BUY" in bb_sig else "inverse"))
                col_idx += 1

            if "VWAP" in selected_indicators and 'VWAP' in latest and pd.notna(latest['VWAP']):
                vwap_sig = "BUY 🟢" if latest['Close'] > latest['VWAP'] else "SELL 🔴"
                metric_cols[col_idx].metric("VWAP", f"{latest['VWAP']:.2f}", delta=vwap_sig, delta_color="normal" if "BUY" in vwap_sig else "inverse")
                col_idx += 1

            st.markdown("##")
            fig = create_stock_chart(df_selected, selected_symbol, selected_symbol, selected_indicators)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})