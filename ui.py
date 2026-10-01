import streamlit as st
from analyzer import WATCHLIST, get_watchlist_summary, analyze_ticker
from visualizer import create_stock_chart

def setup_page():
    st.set_page_config(
        page_title="Algo Trading Dashboard",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for dark-themed, sleek dashboard elements
    st.markdown("""
        <style>
        /* Main background tuning */
        .main {
            background-color: #0e1117;
        }
        /* Custom card styling for metrics */
        div[data-testid="stMetric"] {
            background-color: #1e222d;
            border: 1px solid #2a2e39;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        div[data-testid="stMetric"] label {
            color: #787b86 !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
        }
        div[data-testid="stMetricValue"] {
            color: #d1d4dc !important;
            font-size: 1.6rem !important;
            font-weight: 700 !important;
        }
        /* Clean table headers */
        div[data-testid="stDataFrame"] {
            border: 1px solid #2a2e39;
            border-radius: 8px;
            overflow: hidden;
        }
        /* Remove default gap */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

def render_dashboard():
    # --- SIDEBAR CONTROL PANEL ---
    with st.sidebar:
        st.title("⚡ Control Panel")
        st.caption("Engine Parameters & Controls")
        
        st.markdown("---")
        st.subheader("🎯 Asset Selection")
        selected_company = st.selectbox(
            "Select Asset:",
            options=list(WATCHLIST.keys())
        )
        selected_symbol = WATCHLIST[selected_company]

        st.markdown("---")
        st.markdown("### 📊 Engine Specs")
        st.info("""
        - **Strategy:** SMA Crossover (20/50) + RSI (14)
        - **Data Feed:** YFinance API
        - **Execution:** Paper / Backtest Mode
        """)
        
        if st.button("🔄 Force Refresh Data", use_container_width=True):
            st.rerun()

    # --- MAIN CONTENT AREA ---
    st.title("⚡ Algorithmic Trading Analytics Engine")
    st.caption(f"Real-time Signal Processing & Indicator Deep Dive")

    # High-level System Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tracked Assets", f"{len(WATCHLIST)} Tickers")
    m2.metric("Primary Strategy", "SMA (20/50) + RSI")
    m3.metric("Engine Status", "Online", delta="Operational", delta_color="normal")
    m4.metric("Active Ticker", selected_symbol)

    st.markdown("##")

    # SECTION 1: WATCHLIST OVERVIEW
    st.subheader("📋 Watchlist Signal Matrix")
    with st.spinner("Fetching market data and processing strategy logic..."):
        summary_df = get_watchlist_summary()
        
        if not summary_df.empty:
            # Styled dataframe with full width
            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Signal": st.column_config.TextColumn(
                        "Trade Signal",
                        help="Generated strategy signal",
                    ),
                    "Close": st.column_config.NumberColumn(
                        "Last Price",
                        format="₹%.2f" if "NSE" in str(WATCHLIST) else "$%.2f"
                    )
                }
            )
        else:
            st.warning("No summary data returned from analyzer.")

    st.markdown("##")

    # SECTION 2: DEEP DIVE & CHARTS
    st.subheader(f"🔍 Deep Dive: {selected_company} ({selected_symbol})")
    
    df_selected = analyze_ticker(selected_symbol)

    if df_selected is not None and not df_selected.empty:
        latest_row = df_selected.iloc[-1]
        
        # Indicator Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Current Close", f"{latest_row['Close']:.2f}")
        
        # Color-coded RSI metric indicator logic
        rsi_val = latest_row['RSI']
        rsi_delta = "Overbought (>70)" if rsi_val > 70 else ("Oversold (<30)" if rsi_val < 30 else "Neutral")
        c2.metric("RSI (14)", f"{rsi_val:.2f}", delta=rsi_delta, delta_color="off" if rsi_delta == "Neutral" else "inverse")
        
        c3.metric("SMA 20 (Fast)", f"{latest_row['SMA_20']:.2f}")
        c4.metric("SMA 50 (Slow)", f"{latest_row['SMA_50']:.2f}")

        # Plotly Chart Component
        fig = create_stock_chart(df_selected, selected_company, selected_symbol)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    else:
        st.error(f"Failed to fetch historical indicators for {selected_symbol}.")