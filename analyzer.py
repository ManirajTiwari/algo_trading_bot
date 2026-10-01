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
def analyze_ticker(ticker, period="100mo", interval="1d", initial_capital=100000):
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    
    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # TA Indicators
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)

    # Buy / Sell Signals
    df['Signal'] = 0
    df.loc[(df['SMA_20'] > df['SMA_50']) & (df['RSI'] < 70), 'Signal'] = 1   # BUY
    df.loc[(df['SMA_20'] < df['SMA_50']) | (df['RSI'] > 70), 'Signal'] = -1  # SELL

    # Backtesting Logic
    df['Pct_Change'] = df['Close'].pct_change()
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Pct_Change']
    df['Cumulative_Return'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()
    df['Portfolio_Value'] = initial_capital * df['Cumulative_Return']
    
    return df

def get_watchlist_summary():
    summary_list = []
    
    for name, symbol in WATCHLIST.items():
        df = analyze_ticker(symbol)
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
            
            start_val = float(df['Portfolio_Value'].dropna().iloc[0])
            end_val = float(df['Portfolio_Value'].iloc[-1])
            pnl_pct = ((end_val - start_val) / start_val) * 100
            
            summary_list.append({
                "Company": name,
                "Symbol": symbol,
                "Price": f"${latest_close:,.2f}" if "USD" in symbol else f"₹{latest_close:,.2f}",
                "Signal": action,
                "RSI": round(float(latest['RSI']), 2) if pd.notna(latest['RSI']) else 0,
                "Strategy P&L": f"{pnl_pct:+.2f}%"
            })
            
    return pd.DataFrame(summary_list)