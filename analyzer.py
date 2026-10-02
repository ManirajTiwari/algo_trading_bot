import pandas as pd
import yfinance as yf
import ta
import streamlit as st

# Major Market & Country Index Mappings
MARKET_DATA = {
    "India (NSE & BSE)": {
        "indices": {
            "Nifty 50": "^NSEI",
            "Bank Nifty": "^NSEBANK",
            "BSE Sensex": "^BSESN"
        },
        "tickers": [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
            "BHARTIARTL.NS", "SBIN.NS", "LTIM.NS", "ITC.NS", "HINDUNILVR.NS",
            "LT.NS", "AXISBANK.NS", "KOTAKBANK.NS", "M&M.NS", "TATAMOTORS.NS",
            "SUNPHARMA.NS", "NTPC.NS", "TITAN.NS", "BAJFINANCE.NS", "ULTRACEMCO.NS"
        ]
    },
    "USA (S&P 500 & Nasdaq)": {
        "indices": {
            "S&P 500": "^GSPC",
            "Nasdaq 100": "^IXIC",
            "Dow Jones": "^DJI"
        },
        "tickers": [
            "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
            "META", "TSLA", "BRK-B", "LLY", "AVGO",
            "JPM", "WMT", "V", "MA", "UNH",
            "PG", "HD", "JNJ", "COST", "ORCL"
        ]
    },
    "UK (FTSE 100)": {
        "indices": {
            "FTSE 100": "^FTSE"
        },
        "tickers": [
            "SHEL.L", "AZN.L", "HSBA.L", "ULVR.L", "BP.L",
            "GSK.L", "RIO.L", "REL.L", "BATS.L", "DIAGEO.L"
        ]
    },
    "Japan (Nikkei 225)": {
        "indices": {
            "Nikkei 225": "^N225"
        },
        "tickers": [
            "7203.T", "6758.T", "9984.T", "6861.T", "8306.T",
            "7751.T", "6501.T", "8035.T", "4063.T", "9983.T"
        ]
    }
}

@st.cache_data(ttl=300)
def resolve_ticker(query: str) -> str:
    """Formats or resolves user search query into valid Yahoo Finance ticker."""
    clean = query.strip().upper()
    if clean in ["BTC", "BITCOIN"]: return "BTC-USD"
    if clean in ["ETH", "ETHEREUM"]: return "ETH-USD"
    if clean in ["NIFTY", "NIFTY50", "NIFTY 50"]: return "^NSEI"
    if clean in ["BANKNIFTY", "BANK NIFTY"]: return "^NSEBANK"
    if clean in ["SENSEX", "BSE"]: return "^BSESN"
    return clean

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

    df['Signal'] = 0
    df.loc[(df['SMA_20'] > df['SMA_50']) & (df['RSI'] < 70), 'Signal'] = 1
    df.loc[(df['SMA_20'] < df['SMA_50']) | (df['RSI'] > 70), 'Signal'] = -1

    df['Pct_Change'] = df['Close'].pct_change()
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Pct_Change']
    df['Cumulative_Return'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()
    df['Portfolio_Value'] = initial_capital * df['Cumulative_Return']

    return df

@st.cache_data(ttl=300)
def get_market_overview(country_key, period="1y", top_n=10, indicators=None):
    if indicators is None:
        indicators = ["SMA 20 & 50", "RSI (14)"]

    tickers = MARKET_DATA.get(country_key, {}).get("tickers", [])[:top_n]
    results = []

    for sym in tickers:
        df = analyze_ticker(sym, period=period, indicators=indicators)
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            first = df.iloc[0]

            c_latest = float(latest['Close'])
            c_first = float(first['Close'])
            pct_change = ((c_latest - c_first) / c_first) * 100

            sma_sig = "BUY 🟢" if pd.notna(latest.get('SMA_20')) and latest['SMA_20'] > latest['SMA_50'] else "SELL 🔴"
            rsi_sig = "HOLD 🟡"
            if pd.notna(latest.get('RSI')):
                rsi_sig = "SELL 🔴 (OB)" if latest['RSI'] > 70 else ("BUY 🟢 (OS)" if latest['RSI'] < 30 else "HOLD 🟡")

            results.append({
                "Symbol": sym,
                "Price": f"{c_latest:,.2f}",
                "Period Return (%)": round(pct_change, 2),
                "SMA Signal": sma_sig,
                "RSI Signal": rsi_sig,
                "_raw_return": pct_change
            })

    df_res = pd.DataFrame(results)
    if df_res.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    index_df = df_res.drop(columns=["_raw_return"]).copy()
    
    # Gainers & Losers
    sorted_df = df_res.sort_values(by="_raw_return", ascending=False)
    gainers_df = sorted_df.head(top_n).drop(columns=["_raw_return"]).copy()
    losers_df = df_res.sort_values(by="_raw_return", ascending=True).head(top_n).drop(columns=["_raw_return"]).copy()

    # Compounders
    compounders_df = sorted_df[(sorted_df["_raw_return"] > 0) & (sorted_df["SMA Signal"] == "BUY 🟢")].drop(columns=["_raw_return"]).copy()

    return index_df, gainers_df, losers_df, compounders_df