"""
Chart creation functions using Plotly.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_chart(df: pd.DataFrame, trades: list, focus_idx: int = None, zoom_level: int = 100) -> go.Figure:
    """Cria gráfico de candlestick com indicadores e trades."""
    
    # Subplot com 3 linhas: preço, RSI, MACD
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=('Preço', 'RSI', 'MACD')
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Preço'
        ),
        row=1, col=1
    )
    
    # EMAs
    fig.add_trace(go.Scatter(x=df.index, y=df['ema9'], name='EMA 9', line=dict(color='blue', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema21'], name='EMA 21', line=dict(color='orange', width=1)), row=1, col=1)
    
    # Bollinger Bands
    fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], name='BB Upper', line=dict(color='gray', width=1, dash='dot')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], name='BB Lower', line=dict(color='gray', width=1, dash='dot')), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], name='RSI', line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # MACD
    fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD', line=dict(color='blue')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], name='Signal', line=dict(color='orange')), row=3, col=1)
    
    # Marcadores de trades
    for trade in trades:
        color = 'green' if trade['action'] == 'BUY' else 'red'
        symbol = 'triangle-up' if trade['action'] == 'BUY' else 'triangle-down'
        
        fig.add_trace(
            go.Scatter(
                x=[trade['timestamp']],
                y=[trade['price']],
                mode='markers',
                marker=dict(color=color, size=15, symbol=symbol),
                name=trade['action']
            ),
            row=1, col=1
        )
    
    # Configura Zoom/Range se solicitado
    if focus_idx is not None and focus_idx < len(df):
        visible_candles = zoom_level
        end_idx = min(len(df) - 1, focus_idx + int(visible_candles * 0.1))
        start_idx = max(0, end_idx - visible_candles)
        
        x_min = df.index[start_idx]
        x_max = df.index[end_idx]
        
        fig.update_xaxes(range=[x_min, x_max], row=3, col=1)
        fig.update_xaxes(range=[x_min, x_max], row=2, col=1)
        fig.update_xaxes(range=[x_min, x_max], row=1, col=1)

    fig.update_layout(
        height=800,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        dragmode='pan'
    )
    
    return fig
