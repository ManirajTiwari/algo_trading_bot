import streamlit as st
from analyzer import WATCHLIST, get_watchlist_summary, analyze_ticker
from visualizer import create_stock_chart

def setup_page():
    st.set_page_config(
        page_title="Algo Trading Analytics Dashboard",
        page_icon="📈",
        layout="wide"
    )

def render_dashboard():
    st.title("⚡ Algorithmic Trading Analytics Dashboard")
    st.caption("Minimalist Backtesting & Live Signal Engine")

    # Top Metrics Row
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Active Assets Managed", value=len(WATCHLIST))
    col2.metric(label="Primary Strategy", value="SMA Crossover + RSI")
    col3.metric(label="Engine Status", value="Online 🟢")

    st.markdown("---")
    st.subheader("📋 Watchlist Overview & Signals")

    # Summary Table
    with st.spinner("Fetching market data and running indicators..."):
        summary_df = get_watchlist_summary()
        
        if not summary_df.empty:
            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True
            )

    st.markdown("---")
    st.subheader("🔍 Stock Deep Dive & Interactive Chart Analysis")

    # Stock Selectbox
    selected_company = st.selectbox(
        "विश्लेषण के लिए कंपनी चुनिए (Select Asset to Analyze):",
        options=list(WATCHLIST.keys())
    )

    selected_symbol = WATCHLIST[selected_company]
    df_selected = analyze_ticker(selected_symbol)

    if df_selected is not None and not df_selected.empty:
        # Chart Render
        fig = create_stock_chart(df_selected, selected_company, selected_symbol)
        st.plotly_chart(fig, use_container_width=True)

        # Stats Metrics
        latest_row = df_selected.iloc[-1]
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Current Price", f"{latest_row['Close']:.2f}")
        col_b.metric("RSI Value", f"{latest_row['RSI']:.2f}")
        col_c.metric("SMA 20", f"{latest_row['SMA_20']:.2f}")
        col_d.metric("SMA 50", f"{latest_row['SMA_50']:.2f}")
    else:
        st.error("चुने गए स्टॉक का डेटा लोड नहीं हो सका।")