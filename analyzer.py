import pandas as pd
import yfinance as yf
import ta
import streamlit as st

@st.cache_data(ttl=300)
def search_ticker_symbol(query: str) -> str:
    """Attempts to normalize or find a ticker symbol from user search text."""
    clean_query = query.strip().upper()
    
    # Common crypto/forex/stock mapping helper or raw symbol check
    if clean_query in ["BTC", "BITCOIN"]:
        return "BTC-USD"
    if clean_query in ["ETH", "ETHEREUM"]:
        return "ETH-USD"
    
    # If standard ticker format provided (e.g., RELIANCE.NS, AAPL, TSLA)
    return clean_query

@st.cache_data(ttl=300)
def analyze_ticker(ticker_symbol, period="1y", interval="1d", initial_capital=100000, indicators=None):
    if indicators is None:
        indicators = ["SMA 20 & 50", "RSI (14)", "Volume Bars"]

    try:
        df = yf.download(ticker_symbol, period=period, interval=interval, progress=False)
    except Exception:
        return None

    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Indicator Calculations
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)

    if "MACD" in indicators:
        macd_obj = ta.trend.MACD(df['Close'])
        df['MACD'] = macd_obj.macd()
        df['MACD_Signal'] = macd_obj.macd_signal()
        df['MACD_Hist'] = macd_obj.macd_diff()

    if "Bollinger Bands" in indicators:
        bb_obj = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_Upper'] = bb_obj.bollinger_hband()
        df['BB_Middle'] = bb_obj.bollinger_mavg()
        df['BB_Lower'] = bb_obj.bollinger_lband()

    if "Supertrend" in indicators:
        sti = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=7).average_true_range()
        hl2 = (df['High'] + df['Low']) / 2
        df['Supertrend_Upper'] = hl2 + (3 * sti)
        df['Supertrend_Lower'] = hl2 - (3 * sti)

    if "VWAP" in indicators:
        df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()

    # Base Backtesting Strategy Signal
    df['Signal'] = 0
    df.loc[(df['SMA_20'] > df['SMA_50']) & (df['RSI'] < 70), 'Signal'] = 1   # BUY
    df.loc[(df['SMA_20'] < df['SMA_50']) | (df['RSI'] > 70), 'Signal'] = -1  # SELL

    df['Pct_Change'] = df['Close'].pct_change()
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Pct_Change']
    df['Cumulative_Return'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()
    df['Portfolio_Value'] = initial_capital * df['Cumulative_Return']

    return df

def get_single_summary(symbol, period="1y", indicators=None):
    if indicators is None:
        indicators = ["SMA 20 & 50", "RSI (14)", "Volume Bars"]

    df = analyze_ticker(symbol, period=period, indicators=indicators)
    if df is None or df.empty:
        return pd.DataFrame()

    latest = df.iloc[-1]
    latest_close = float(latest['Close'])

    row = {
        "Symbol": symbol,
        "Price": f"${latest_close:,.2f}" if "USD" in symbol else f"₹{latest_close:,.2f}"
    }

    if "SMA 20 & 50" in indicators and pd.notna(latest['SMA_20']) and pd.notna(latest['SMA_50']):
        row["SMA Signal"] = "BUY 🟢" if latest['SMA_20'] > latest['SMA_50'] else "SELL 🔴"

    if "RSI (14)" in indicators and pd.notna(latest['RSI']):
        rsi_val = latest['RSI']
        if rsi_val > 70:
            row["RSI Signal"] = "SELL 🔴 (Overbought)"
        elif rsi_val < 30:
            row["RSI Signal"] = "BUY 🟢 (Oversold)"
        else:
            row["RSI Signal"] = "HOLD 🟡 (Neutral)"

    if "MACD" in indicators and 'MACD' in df.columns and pd.notna(latest['MACD']):
        row["MACD Signal"] = "BUY 🟢" if latest['MACD'] > latest['MACD_Signal'] else "SELL 🔴"

    if "Bollinger Bands" in indicators and 'BB_Upper' in df.columns and pd.notna(latest['BB_Upper']):
        if latest['Close'] >= latest['BB_Upper']:
            row["BB Signal"] = "SELL 🔴 (Overbought)"
        elif latest['Close'] <= latest['BB_Lower']:
            row["BB Signal"] = "BUY 🟢 (Oversold)"
        else:
            row["BB Signal"] = "HOLD 🟡"

    if "VWAP" in indicators and 'VWAP' in df.columns and pd.notna(latest['VWAP']):
        row["VWAP Signal"] = "BUY 🟢" if latest['Close'] > latest['VWAP'] else "SELL 🔴"

    valid_p = df['Portfolio_Value'].dropna()
    pnl_pct = ((float(valid_p.iloc[-1]) - float(valid_p.iloc[0])) / float(valid_p.iloc[0])) * 100 if not valid_p.empty else 0.0
    row["Strategy P&L"] = f"{pnl_pct:+.2f}%"

    return pd.DataFrame([row])