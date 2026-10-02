import streamlit as st
import pandas as pd
from analyzer import MARKET_DATA, resolve_ticker, get_market_overview, analyze_ticker
from visualizer import create_stock_chart

def setup_page():
    st.set_page_config(
        page_title="Global Algo Trading Analytics",
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
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        </style>
    """, unsafe_allow_html=True)

def render_dashboard():
    setup_page()

    # --- SIDEBAR CONTROL PANEL ---
    with st.sidebar:
        st.title("⚡ Control Panel")

        st.markdown("---")
        st.subheader("🔍 Universal Search")
        search_query = st.text_input(
            "Search Company / Ticker:",
            value="",
            placeholder="e.g. TATAMOTORS.NS, AAPL, BTC-USD...",
            help="For Indian NSE stocks, add '.NS'. For US stocks, use ticker symbol directly."
        )

        st.markdown("---")
        st.subheader("🌐 Market & Country Selector")
        selected_country = st.selectbox(
            "Select Country Market:",
            options=list(MARKET_DATA.keys()),
            index=0
        )

        st.markdown("---")
        st.subheader("📊 Filters & Timeframe")
        top_n = st.slider("Company Limit (Top N):", min_value=5, max_value=20, value=10, step=5)

        timeframe_map = {
            "1 Day": "1d",
            "1 Week": "5d",
            "1 Month": "1mo",
            "1 Year": "1y",
            "5 Years": "5y"
        }
        tf_label = st.selectbox("Select Timeframe:", options=list(timeframe_map.keys()), index=3)
        selected_period = timeframe_map[tf_label]

        st.markdown("---")
        st.subheader("🛠️ Indicator Strategy")
        selected_indicators = st.multiselect(
            "Active Indicators:",
            options=["SMA 20 & 50", "RSI (14)", "MACD", "Bollinger Bands", "Volume Bars", "VWAP", "Supertrend"],
            default=["SMA 20 & 50", "RSI (14)", "MACD", "Volume Bars"]
        )

        st.markdown("---")
        if st.button("🔄 Force Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # --- MAIN DASHBOARD HEADER ---
    st.title("⚡ Algorithmic Trading Engine")

    # SECTION 1: SEARCH OVERRIDE OR MAJOR INDEX CARDS
    if search_query.strip():
        resolved_sym = resolve_ticker(search_query)
        st.subheader(f"🎯 Search Result: **{resolved_sym}**")
        df_search = analyze_ticker(resolved_sym, period=selected_period, indicators=selected_indicators)
        if df_search is not None and not df_search.empty:
            latest = df_search.iloc[-1]
            cols = st.columns(4)
            cols[0].metric("Last Price", f"{latest['Close']:.2f}")
            cols[1].metric("RSI (14)", f"{latest['RSI']:.2f}" if pd.notna(latest.get('RSI')) else "N/A")
            cols[2].metric("SMA 20", f"{latest['SMA_20']:.2f}" if pd.notna(latest.get('SMA_20')) else "N/A")
            cols[3].metric("SMA 50", f"{latest['SMA_50']:.2f}" if pd.notna(latest.get('SMA_50')) else "N/A")

            st.markdown("##")
            fig = create_stock_chart(df_search, resolved_sym, resolved_sym, selected_indicators)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown("---")
        else:
            st.error(f"Could not load market data for '{resolved_sym}'. Ensure valid symbol syntax.")
            st.markdown("---")

    # SECTION 2: MAJOR COUNTRY INDEX CARDS (Nifty 50, Bank Nifty, BSE Sensex, etc.)
    st.subheader(f"🏛️ Major Indices ({selected_country})")
    indices_dict = MARKET_DATA[selected_country]["indices"]
    idx_cols = st.columns(len(indices_dict))

    for col, (idx_name, idx_sym) in zip(idx_cols, indices_dict.items()):
        df_idx = analyze_ticker(idx_sym, period=selected_period)
        if df_idx is not None and not df_idx.empty:
            l_close = float(df_idx['Close'].iloc[-1])
            f_close = float(df_idx['Close'].iloc[0])
            change_pct = ((l_close - f_close) / f_close) * 100
            col.metric(idx_name, f"{l_close:,.2f}", delta=f"{change_pct:+.2f}%")

    st.markdown("---")

    # SECTION 3: MARKET DATA TABS (Gainers, Losers, Index Stocks, Compounders)
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Top Gainers",
        "🔻 Top Losers",
        "📋 Major Index Stocks",
        "💎 Long-Term Compounders"
    ])

    with st.spinner(f"Fetching top {top_n} assets for {selected_country}..."):
        index_df, gainers_df, losers_df, compounders_df = get_market_overview(
            country_key=selected_country,
            period=selected_period,
            top_n=top_n,
            indicators=selected_indicators
        )

    with tab1:
        st.subheader(f"Top {top_n} Gainers ({tf_label})")
        if not gainers_df.empty:
            st.dataframe(gainers_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No data found.")

    with tab2:
        st.subheader(f"Top {top_n} Losers ({tf_label})")
        if not losers_df.empty:
            st.dataframe(losers_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No data found.")

    with tab3:
        st.subheader(f"Major Index Constituents ({selected_country})")
        if not index_df.empty:
            st.dataframe(index_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No data found.")

    with tab4:
        st.subheader("Long-Term / Compounders Filter")
        st.caption("Companies maintaining positive net returns and SMA bullish alignment.")
        if not compounders_df.empty:
            st.dataframe(compounders_df, use_container_width=True, hide_index=True)
        else:
            st.info("No companies matched the compounder filter criteria.")

    st.markdown("---")

    # SECTION 4: SINGLE TICKER DEEP DIVE
    st.subheader("🔍 Deep Dive & Visualizer")
    available_tickers = MARKET_DATA[selected_country]["tickers"][:top_n]
    deep_dive_sym = st.selectbox("Select Stock to Analyze:", options=available_tickers)

    df_deep = analyze_ticker(deep_dive_sym, period=selected_period, indicators=selected_indicators)
    if df_deep is not None and not df_deep.empty:
        fig_deep = create_stock_chart(df_deep, deep_dive_sym, deep_dive_sym, selected_indicators)
        st.plotly_chart(fig_deep, use_container_width=True, config={'displayModeBar': False})