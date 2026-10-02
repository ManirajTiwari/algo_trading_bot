import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_stock_chart(df_selected, company_name, symbol, selected_indicators=None):
    if selected_indicators is None:
        selected_indicators = ["SMA 20 & 50", "RSI (14)", "Volume Bars"]

    # 1. Determine active lower subplots
    has_rsi = "RSI (14)" in selected_indicators and 'RSI' in df_selected.columns
    has_macd = "MACD" in selected_indicators and 'MACD' in df_selected.columns
    has_volume = "Volume Bars" in selected_indicators and 'Volume' in df_selected.columns

    extra_rows = sum([has_rsi, has_macd, has_volume])
    total_rows = 1 + extra_rows

    # 2. Dynamic row height calculation
    if extra_rows > 0:
        main_height = 0.55
        sub_height = (1.0 - main_height) / extra_rows
        row_heights = [main_height] + [sub_height] * extra_rows
    else:
        row_heights = [1.0]

    # 3. Dynamic Subplot Titles
    subplot_titles = [f"{company_name} ({symbol}) Price & Overlay Signals"]
    if has_rsi: subplot_titles.append("RSI (14)")
    if has_macd: subplot_titles.append("MACD")
    if has_volume: subplot_titles.append("Volume")

    # 4. Construct Subplot Grid
    fig = make_subplots(
        rows=total_rows, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.04, 
        row_heights=row_heights,
        subplot_titles=subplot_titles
    )

    # --- MAIN CHART (Row 1) ---
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df_selected.index,
        open=df_selected['Open'],
        high=df_selected['High'],
        low=df_selected['Low'],
        close=df_selected['Close'],
        name="OHLC"
    ), row=1, col=1)

    # SMA 20 & 50
    if "SMA 20 & 50" in selected_indicators:
        if 'SMA_20' in df_selected.columns:
            fig.add_trace(go.Scatter(
                x=df_selected.index, y=df_selected['SMA_20'],
                line=dict(color='orange', width=1.2), name="SMA 20"
            ), row=1, col=1)
        if 'SMA_50' in df_selected.columns:
            fig.add_trace(go.Scatter(
                x=df_selected.index, y=df_selected['SMA_50'],
                line=dict(color='blue', width=1.2), name="SMA 50"
            ), row=1, col=1)

    # Bollinger Bands
    if "Bollinger Bands" in selected_indicators and 'BB_Upper' in df_selected.columns:
        fig.add_trace(go.Scatter(
            x=df_selected.index, y=df_selected['BB_Upper'],
            line=dict(color='rgba(173, 216, 230, 0.4)', width=1, dash='dash'), name="BB Upper"
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df_selected.index, y=df_selected['BB_Lower'],
            line=dict(color='rgba(173, 216, 230, 0.4)', width=1, dash='dash'), name="BB Lower"
        ), row=1, col=1)

    # VWAP
    if "VWAP" in selected_indicators and 'VWAP' in df_selected.columns:
        fig.add_trace(go.Scatter(
            x=df_selected.index, y=df_selected['VWAP'],
            line=dict(color='magenta', width=1.3), name="VWAP"
        ), row=1, col=1)

    # Supertrend
    if "Supertrend" in selected_indicators and 'Supertrend_Upper' in df_selected.columns:
        fig.add_trace(go.Scatter(
            x=df_selected.index, y=df_selected['Supertrend_Upper'],
            line=dict(color='red', width=1), name="ST Upper"
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df_selected.index, y=df_selected['Supertrend_Lower'],
            line=dict(color='green', width=1), name="ST Lower"
        ), row=1, col=1)

    # --- INDICATOR SIGNAL MARKERS ON PRICE CHART ---
    # 1. Composite Strategy Signals (Green Triangle Up / Red Triangle Down)
    if 'Signal' in df_selected.columns:
        buy_signals = df_selected[df_selected['Signal'] == 1]
        sell_signals = df_selected[df_selected['Signal'] == -1]

        if not buy_signals.empty:
            fig.add_trace(go.Scatter(
                x=buy_signals.index,
                y=buy_signals['Low'] * 0.98,
                mode='markers',
                marker=dict(symbol='triangle-up', size=12, color='#00E676'),
                name='Strategy BUY'
            ), row=1, col=1)

        if not sell_signals.empty:
            fig.add_trace(go.Scatter(
                x=sell_signals.index,
                y=sell_signals['High'] * 1.02,
                mode='markers',
                marker=dict(symbol='triangle-down', size=12, color='#FF5252'),
                name='Strategy SELL'
            ), row=1, col=1)

    # 2. RSI Extreme Threshold Markers
    if has_rsi:
        rsi_overbought = df_selected[df_selected['RSI'] >= 70]
        rsi_oversold = df_selected[df_selected['RSI'] <= 30]

        if not rsi_oversold.empty:
            fig.add_trace(go.Scatter(
                x=rsi_oversold.index,
                y=rsi_oversold['Low'] * 0.97,
                mode='markers',
                marker=dict(symbol='circle', size=7, color='#00E676', line=dict(width=1, color='white')),
                name='RSI Oversold (Buy)'
            ), row=1, col=1)

        if not rsi_overbought.empty:
            fig.add_trace(go.Scatter(
                x=rsi_overbought.index,
                y=rsi_overbought['High'] * 1.03,
                mode='markers',
                marker=dict(symbol='circle', size=7, color='#FF5252', line=dict(width=1, color='white')),
                name='RSI Overbought (Sell)'
            ), row=1, col=1)

    # --- LOWER SUBPLOTS ---
    current_row = 2

    # RSI Subplot
    if has_rsi:
        fig.add_trace(go.Scatter(
            x=df_selected.index, y=df_selected['RSI'],
            line=dict(color='mediumpurple', width=1.5), name="RSI"
        ), row=current_row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#FF5252", row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#00E676", row=current_row, col=1)
        fig.update_yaxes(range=[0, 100], row=current_row, col=1)
        current_row += 1

    # MACD Subplot
    if has_macd:
        fig.add_trace(go.Scatter(
            x=df_selected.index, y=df_selected['MACD'],
            line=dict(color='cyan', width=1.5), name="MACD"
        ), row=current_row, col=1)
        fig.add_trace(go.Scatter(
            x=df_selected.index, y=df_selected['MACD_Signal'],
            line=dict(color='orange', width=1.5), name="MACD Signal"
        ), row=current_row, col=1)
        
        hist_colors = ['#00E676' if val >= 0 else '#FF5252' for val in df_selected['MACD_Hist'].fillna(0)]
        fig.add_trace(go.Bar(
            x=df_selected.index, y=df_selected['MACD_Hist'],
            marker_color=hist_colors, name="MACD Hist"
        ), row=current_row, col=1)
        current_row += 1

    # Volume Subplot
    if has_volume:
        vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df_selected['Close'], df_selected['Open'])]
        fig.add_trace(go.Bar(
            x=df_selected.index, y=df_selected['Volume'],
            marker_color=vol_colors, name="Volume"
        ), row=current_row, col=1)
        current_row += 1

    # --- LAYOUT FORMATTING ---
    fig.update_layout(
        height=420 + (180 * extra_rows),
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig