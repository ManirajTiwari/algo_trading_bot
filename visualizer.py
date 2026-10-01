import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_stock_chart(df_selected, company_name, symbol):
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.08, 
        row_heights=[0.7, 0.3],
        subplot_titles=(f"{company_name} ({symbol}) Price & Moving Averages", "RSI (14) Indicator")
    )

    # 1. Candlestick Chart
    fig.add_trace(go.Candlestick(
        x=df_selected.index,
        open=df_selected['Open'],
        high=df_selected['High'],
        low=df_selected['Low'],
        close=df_selected['Close'],
        name="OHLC"
    ), row=1, col=1)

    # 2. SMA 20
    fig.add_trace(go.Scatter(
        x=df_selected.index,
        y=df_selected['SMA_20'],
        line=dict(color='orange', width=1.5),
        name="SMA 20"
    ), row=1, col=1)

    # 3. SMA 50
    fig.add_trace(go.Scatter(
        x=df_selected.index,
        y=df_selected['SMA_50'],
        line=dict(color='blue', width=1.5),
        name="SMA 50"
    ), row=1, col=1)

    # 4. RSI Chart
    fig.add_trace(go.Scatter(
        x=df_selected.index,
        y=df_selected['RSI'],
        line=dict(color='purple', width=1.5),
        name="RSI"
    ), row=2, col=1)

    # RSI Lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # Layout
    fig.update_layout(
        height=650,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig