import pandas as pd
import yfinance as yf
import ta
import streamlit as st

WATCHLIST = {
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD"
}

@st.cache_data(ttl=300)
def analyze_ticker(ticker, period="1y", interval="1d", initial_capital=100000):
    # Always fetch enough history (e.g., min 1y) so SMA_50 and RSI compute cleanly,
    # then slice to the target period if needed.
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    
    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Technical Indicators
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)

    # Buy / Sell Signals
    df['Signal'] = 0
    df.loc[(df['SMA_20'] > df['SMA_50']) & (df['RSI'] < 70), 'Signal'] = 1   # BUY
    df.loc[(df['SMA_20'] < df['SMA_50']) | (df['RSI'] > 70), 'Signal'] = -1  # SELL

    # Backtesting Logic (Shifted by 1 to prevent look-ahead bias)
    df['Pct_Change'] = df['Close'].pct_change()
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Pct_Change']
    df['Cumulative_Return'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()
    df['Portfolio_Value'] = initial_capital * df['Cumulative_Return']
    
    return df

def get_watchlist_summary(period="1y"):
    summary_list = []
    
    for name, symbol in WATCHLIST.items():
        # Pass period explicitly to avoid pulling default arguments
        df = analyze_ticker(symbol, period=period)
        
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            latest_close = float(latest['Close'])
            signal_code = int(latest['Signal'])
            
            if signal_code == 1:
                action = "BUY 🟢"
            elif signal_code == -1:
                action = "SELL 🔴"
            else:
                action = "HOLD 🟡"
            
            valid_portfolio = df['Portfolio_Value'].dropna()
            if not valid_portfolio.empty:
                start_val = float(valid_portfolio.iloc[0])
                end_val = float(valid_portfolio.iloc[-1])
                pnl_pct = ((end_val - start_val) / start_val) * 100
            else:
                pnl_pct = 0.0
            
            summary_list.append({
                "Company": name,
                "Symbol": symbol,
                "Price": f"${latest_close:,.2f}" if "USD" in symbol else f"₹{latest_close:,.2f}",
                "Signal": action,
                "RSI": round(float(latest['RSI']), 2) if pd.notna(latest['RSI']) else 0,
                "Strategy P&L": f"{pnl_pct:+.2f}%"
            })
            
    return pd.DataFrame(summary_list)

# --- Streamlit UI Integration ---
st.title("Watchlist & Strategy Backtester")

# Sidebar for dynamic time period selection
selected_period = st.sidebar.selectbox(
    "Select Duration",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3  # Default to "1y" so SMA_50 has enough data
)

# Render Summary Table
st.subheader(f"Watchlist Summary ({selected_period})")
summary_df = get_watchlist_summary(period=selected_period)
st.dataframe(summary_df, use_container_width=True)