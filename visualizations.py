"""
Visualization Module
Chart creation functions optimized for dark theme with light colors
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

COLORS = {
    'primary': '#1d9bf0',      # Twitter blue
    'secondary': '#00ba7c',    # Green  
    'accent': '#7856ff',       # Purple
    'warning': '#ffad1f',      # Yellow/Gold
    'danger': '#f4212e',       # Red
    'purple': '#7856ff',       # Purple
    'orange': '#ff7a00',       # Orange
    'cyan': '#1d9bf0',         # Blue
    'text': '#e7e9ea',         # Light gray text
    'grid': '#2f3336',         # Dark grid
    'background': '#15202b',   # Dark blue bg
    'paper': '#192734',        # Slightly lighter bg
}

# Professional chart template
CHART_TEMPLATE = {
    'layout': {
        'template': 'plotly_dark',
        'paper_bgcolor': COLORS['background'],
        'plot_bgcolor': COLORS['paper'],
        'font': {'color': COLORS['text'], 'family': 'Inter, -apple-system, sans-serif'},
        'xaxis': {'gridcolor': COLORS['grid'], 'gridwidth': 1},
        'yaxis': {'gridcolor': COLORS['grid'], 'gridwidth': 1},
        'hovermode': 'x unified',
    }
}


def create_ohlc_chart(df: pd.DataFrame, symbols: list) -> go.Figure:
    """
    Create OHLC candlestick chart with dual-axis volume
    
    Args:
        df: DataFrame with OHLC data
        symbols: List of symbols to plot
    
    Returns:
        Plotly figure
    """
    symbols = list(symbols)
    use_secondary = len(symbols) > 1
    
    # Both price and volume subplots support secondary y-axis when 2+ symbols
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=('Price', 'Volume'),
        row_heights=[0.7, 0.3],
        specs=[[{"secondary_y": use_secondary}], [{"secondary_y": use_secondary}]],
    )
    
    # Color palette for multiple symbols
    colors = [COLORS['primary'], COLORS['secondary'], COLORS['accent'], 
              COLORS['purple'], COLORS['orange']]
    
    for idx, symbol in enumerate(symbols):
        sdf = df[df['symbol'] == symbol].sort_values('datetime')
        secondary_axis = use_secondary and idx == 1
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=sdf['datetime'],
                open=sdf['open'],
                high=sdf['high'],
                low=sdf['low'],
                close=sdf['close'],
                name=symbol.upper(),
                increasing_line_color=COLORS['secondary'],
                decreasing_line_color=COLORS['danger'],
            ),
            row=1, col=1,
            secondary_y=secondary_axis,
        )
        
        # Volume bars - each symbol on its own axis
        fig.add_trace(
            go.Bar(
                x=sdf['datetime'],
                y=sdf['volume'],
                name=f'{symbol.upper()} Vol',
                marker_color=colors[idx % len(colors)],
                opacity=0.7,
            ),
            row=2, col=1,
            secondary_y=secondary_axis,
        )
    
    # Update axes labels
    fig.update_xaxes(title_text="Time", row=2, col=1, gridcolor=COLORS['grid'])
    
    # Price axes
    if symbols:
        fig.update_yaxes(title_text=f"{symbols[0].upper()} Price", row=1, col=1, 
                        secondary_y=False, gridcolor=COLORS['grid'])
    if use_secondary:
        fig.update_yaxes(title_text=f"{symbols[1].upper()} Price", row=1, col=1, 
                        secondary_y=True, gridcolor=COLORS['grid'])
    
    # Volume axes - separate for each symbol
    if symbols:
        fig.update_yaxes(title_text=f"{symbols[0].upper()} Vol", row=2, col=1, 
                        secondary_y=False, gridcolor=COLORS['grid'])
    if use_secondary:
        fig.update_yaxes(title_text=f"{symbols[1].upper()} Vol", row=2, col=1, 
                        secondary_y=True, gridcolor=COLORS['grid'])
    
    # Calculate the actual data range for x-axis
    all_datetimes = []
    for symbol in symbols:
        sdf = df[df['symbol'] == symbol]
        if not sdf.empty:
            all_datetimes.extend(sdf['datetime'].tolist())
    
    # Set x-axis range to fit data exactly
    x_range = None
    if all_datetimes:
        x_min = min(all_datetimes)
        x_max = max(all_datetimes)
        # Add small padding (5% on each side)
        if hasattr(x_max, 'timestamp'):
            time_span = (x_max - x_min).total_seconds()
            padding = pd.Timedelta(seconds=time_span * 0.05) if time_span > 0 else pd.Timedelta(seconds=60)
            x_range = [x_min - padding, x_max + padding]
    
    # Update layout - Professional dark theme
    fig.update_layout(
        height=700,
        template='plotly_dark',
        paper_bgcolor=COLORS['background'],
        plot_bgcolor=COLORS['paper'],
        font=dict(color=COLORS['text'], family='Inter, sans-serif'),
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(21, 32, 43, 0.9)',
            bordercolor='rgba(56, 68, 77, 0.5)',
            borderwidth=1,
            font=dict(color=COLORS['text'])
        ),
        bargap=0.1,
    )
    
    # Set x-axis range explicitly to focus on data
    if x_range:
        fig.update_xaxes(range=x_range, gridcolor=COLORS['grid'])
        fig.update_xaxes(range=x_range, row=2, col=1, gridcolor=COLORS['grid'])
    else:
        fig.update_xaxes(autorange=True, gridcolor=COLORS['grid'])
    
    fig.update_yaxes(gridcolor=COLORS['grid'], autorange=True)
    
    return fig


def create_single_ohlc_chart(df: pd.DataFrame, symbol: str, show_volume: bool = True, 
                              time_window_seconds: int = None, time_offset_seconds: int = 0) -> go.Figure:
    """
    Create OHLC candlestick chart for a single symbol
    
    Args:
        df: DataFrame with OHLC data
        symbol: Symbol to plot
        show_volume: Whether to show volume subplot
        time_window_seconds: Optional, show N seconds window of data
        time_offset_seconds: Scroll offset - how many seconds back from latest
    
    Returns:
        Plotly figure
    """
    sdf = df[df['symbol'] == symbol].sort_values('datetime')
    
    # Apply time window and offset for scrolling
    if time_window_seconds and not sdf.empty:
        latest_time = sdf['datetime'].max()
        # Apply offset (scroll back in time)
        end_time = latest_time - pd.Timedelta(seconds=time_offset_seconds)
        start_time = end_time - pd.Timedelta(seconds=time_window_seconds)
        sdf = sdf[(sdf['datetime'] >= start_time) & (sdf['datetime'] <= end_time)]
    
    if sdf.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"{symbol.upper()} - No Data",
            template='plotly_dark',
            paper_bgcolor=COLORS['background'],
            plot_bgcolor=COLORS['paper'],
        )
        return fig
    
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.75, 0.25],
        )
    else:
        fig = go.Figure()
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=sdf['datetime'],
            open=sdf['open'],
            high=sdf['high'],
            low=sdf['low'],
            close=sdf['close'],
            name=symbol.upper(),
            increasing_line_color=COLORS['secondary'],
            decreasing_line_color=COLORS['danger'],
            increasing_fillcolor=COLORS['secondary'],
            decreasing_fillcolor=COLORS['danger'],
        ),
        row=1 if show_volume else None,
        col=1 if show_volume else None,
    )
    
    # Volume bars
    if show_volume:
        colors = [COLORS['secondary'] if sdf['close'].iloc[i] >= sdf['open'].iloc[i] 
                  else COLORS['danger'] for i in range(len(sdf))]
        
        fig.add_trace(
            go.Bar(
                x=sdf['datetime'],
                y=sdf['volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.7,
            ),
            row=2, col=1,
        )
    
    # Calculate x-axis range
    x_range = None
    if not sdf.empty:
        x_min = sdf['datetime'].min()
        x_max = sdf['datetime'].max()
        time_span = (x_max - x_min).total_seconds()
        padding = pd.Timedelta(seconds=time_span * 0.05) if time_span > 0 else pd.Timedelta(seconds=60)
        x_range = [x_min - padding, x_max + padding]
    
    # Calculate Y-axis range with TIGHT padding for visible candle bodies
    # Goal: Candles should take up ~80% of vertical height
    y_range = None
    if not sdf.empty:
        price_min = sdf['low'].min()
        price_max = sdf['high'].max()
        price_range = price_max - price_min
        
        # If no price movement, create artificial range around current price
        if price_range == 0 or price_range < 0.01:
            center = (price_min + price_max) / 2
            # Create ~0.01% range for flat prices
            price_range = center * 0.0001
            price_min = center - price_range / 2
            price_max = center + price_range / 2
        
        # Tight padding: 10% of price range on each side
        # This makes candles occupy ~80% of vertical height
        y_padding = price_range * 0.1
        y_range = [price_min - y_padding, price_max + y_padding]
    
    # Layout
    fig.update_layout(
        title=dict(text=f"{symbol.upper()} Price (USD)", font=dict(color='#FFFFFF')),
        height=450,
        template='plotly_dark',
        paper_bgcolor=COLORS['background'],
        plot_bgcolor=COLORS['paper'],
        font=dict(color=COLORS['text'], family='Inter, sans-serif'),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50),  # Increase bottom margin for footer
    )
    
    # Update axes with calculated ranges - FORCE the Y range
    if x_range:
        fig.update_xaxes(range=x_range, gridcolor=COLORS['grid'])
    
    # Explicitly set tight Y-axis range ONLY for the Price subplot (row 1)
    if y_range:
        fig.update_yaxes(range=y_range, row=1, col=1, gridcolor=COLORS['grid'], autorange=False, fixedrange=False)
    else:
        fig.update_yaxes(gridcolor=COLORS['grid'], autorange=True, row=1, col=1)
    
    # Ensure Volume subplot (row 2) is auto-scaled with title
    if show_volume:
        fig.update_yaxes(title_text="Volume", gridcolor=COLORS['grid'], autorange=True, row=2, col=1)
        # Add a footer-like annotation for Volume if needed, or rely on axis title
        # Axis title "Volume" on the secondary plot is standard.
    
    return fig

def create_spread_chart(spread: pd.Series, zscore: pd.Series, 
                       s1: str, s2: str) -> go.Figure:
    """
    Create spread and z-score chart
    
    Args:
        spread: Spread series
        zscore: Z-score series
        s1: First symbol
        s2: Second symbol
    
    Returns:
        Plotly figure
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(f'Spread: {s1.upper()} vs {s2.upper()}', 'Z-Score'),
        row_heights=[0.5, 0.5]
    )
    
    # Spread line
    fig.add_trace(
        go.Scatter(
            x=spread.index,
            y=spread.values,
            name='Spread',
            line=dict(color=COLORS['primary'], width=2),
            fill='tozeroy',
            fillcolor=f'rgba(96, 165, 250, 0.2)'
        ),
        row=1, col=1
    )
    
    # Z-score line
    fig.add_trace(
        go.Scatter(
            x=zscore.index,
            y=zscore.values,
            name='Z-Score',
            line=dict(color=COLORS['purple'], width=2)
        ),
        row=2, col=1
    )
    
    # Threshold lines
    fig.add_hline(y=2, line_dash="dash", line_color=COLORS['danger'], 
                 line_width=2, row=2, col=1, annotation_text="Entry +2σ",
                 annotation_font_color=COLORS['text'])
    fig.add_hline(y=-2, line_dash="dash", line_color=COLORS['danger'], 
                 line_width=2, row=2, col=1, annotation_text="Entry -2σ",
                 annotation_font_color=COLORS['text'])
    fig.add_hline(y=0, line_dash="dot", line_color=COLORS['text'], 
                 line_width=1, row=2, col=1)
    
    # Update axes
    fig.update_xaxes(title_text="Time", row=2, col=1, gridcolor=COLORS['grid'])
    fig.update_yaxes(title_text="Spread", row=1, col=1, gridcolor=COLORS['grid'], autorange=True)
    fig.update_yaxes(title_text="Z-Score", row=2, col=1, gridcolor=COLORS['grid'])
    
    # Update layout
    fig.update_layout(
        height=600,
        **CHART_TEMPLATE['layout'],
        showlegend=True,
        legend=dict(font=dict(color=COLORS['text']))
    )
    
    return fig


def create_correlation_heatmap(df: pd.DataFrame, symbols: list) -> go.Figure:
    """
    Create correlation heatmap
    
    Args:
        df: DataFrame with price data
        symbols: List of symbols
    
    Returns:
        Plotly figure
    """
    pivot = df.pivot_table(values='close', index='datetime', columns='symbol')
    corr = pivot[symbols].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=[s.upper() for s in corr.columns],
        y=[s.upper() for s in corr.columns],
        colorscale='RdBu',
        zmid=0,
        text=np.round(corr.values, 3),
        texttemplate='%{text}',
        textfont={"size": 14, "color": COLORS['text']},
        colorbar=dict(
            title=dict(text="Correlation", font=dict(color=COLORS['text'])),
            tickfont=dict(color=COLORS['text'])
        )
    ))
    
    fig.update_layout(
        title=dict(text='Correlation Matrix', font=dict(color=COLORS['text'], size=20)),
        height=500,
        template='plotly_dark',
        paper_bgcolor=COLORS['background'],
        plot_bgcolor=COLORS['paper'],
        font=dict(color=COLORS['text'], family='Inter, sans-serif'),
    )
    
    fig.update_xaxes(tickfont=dict(color=COLORS['text']))
    fig.update_yaxes(tickfont=dict(color=COLORS['text']))
    
    return fig


def create_backtest_chart(trades_df: pd.DataFrame, positions: pd.Series, 
                         spread: pd.Series) -> go.Figure:
    """
    Create backtest visualization with signals
    
    Args:
        trades_df: DataFrame with trade log
        positions: Position series
        spread: Spread series
    
    Returns:
        Plotly figure
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('Spread with Entry/Exit Signals', 'Position & Cumulative P&L'),
        row_heights=[0.5, 0.5]
    )
    
    # Spread line
    fig.add_trace(
        go.Scatter(
            x=spread.index,
            y=spread.values,
            name='Spread',
            line=dict(color=COLORS['primary'], width=1),
            opacity=0.7
        ),
        row=1, col=1
    )
    
    # Entry/exit markers
    if not trades_df.empty:
        longs = trades_df[trades_df['side'] == 'long']
        shorts = trades_df[trades_df['side'] == 'short']
        
        if not longs.empty:
            fig.add_trace(
                go.Scatter(
                    x=longs['entry_time'],
                    y=longs['entry_price'],
                    mode='markers',
                    name='Long Entry',
                    marker=dict(color=COLORS['secondary'], size=12, symbol='triangle-up'),
                ),
                row=1, col=1
            )
        
        if not shorts.empty:
            fig.add_trace(
                go.Scatter(
                    x=shorts['entry_time'],
                    y=shorts['entry_price'],
                    mode='markers',
                    name='Short Entry',
                    marker=dict(color=COLORS['danger'], size=12, symbol='triangle-down'),
                ),
                row=1, col=1
            )
    
    # Position line
    fig.add_trace(
        go.Scatter(
            x=positions.index,
            y=positions.values,
            name='Position',
            line=dict(color=COLORS['purple'], width=2),
            fill='tozeroy',
            fillcolor=f'rgba(167, 139, 250, 0.2)'
        ),
        row=2, col=1
    )
    
    # Cumulative P&L
    if not trades_df.empty and 'pnl' in trades_df.columns:
        cum_pnl = trades_df['pnl'].fillna(0).cumsum()
        fig.add_trace(
            go.Scatter(
                x=trades_df['exit_time'],
                y=cum_pnl,
                name='Cumulative P&L',
                line=dict(color=COLORS['secondary'], width=3),
                yaxis='y2'
            ),
            row=2, col=1
        )
    
    # Update layout
    fig.update_layout(
        height=700,
        **CHART_TEMPLATE['layout'],
        legend=dict(font=dict(color=COLORS['text']))
    )
    
    fig.update_xaxes(gridcolor=COLORS['grid'])
    fig.update_yaxes(gridcolor=COLORS['grid'])
    
    return fig


def create_distribution_chart(data: pd.Series, title: str = "Distribution") -> go.Figure:
    """
    Create distribution histogram
    
    Args:
        data: Data series
        title: Chart title
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(
        go.Histogram(
            x=data,
            nbinsx=50,
            name='Distribution',
            marker_color=COLORS['primary'],
            opacity=0.7
        )
    )
    
    # Add mean line
    mean_val = data.mean()
    fig.add_vline(
        x=mean_val,
        line_dash="dash",
        line_color=COLORS['warning'],
        line_width=2,
        annotation_text=f"Mean: {mean_val:.4f}",
        annotation_font_color=COLORS['text']
    )
    
    fig.update_layout(
        title=dict(text=f'{title}', font=dict(color=COLORS['text'], size=20)),
        xaxis_title=title,
        yaxis_title="Frequency",
        height=400,
        **CHART_TEMPLATE['layout'],
        showlegend=False
    )
    
    return fig


def create_rolling_correlation_chart(corr: pd.Series, s1: str, s2: str, 
                                     window: int) -> go.Figure:
    """
    Create rolling correlation chart
    
    Args:
        corr: Rolling correlation series
        s1: First symbol
        s2: Second symbol
        window: Rolling window size
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=corr.index,
            y=corr.values,
            mode='lines',
            name='Correlation',
            line=dict(color=COLORS['orange'], width=2),
            fill='tozeroy',
            fillcolor=f'rgba(251, 146, 60, 0.2)'
        )
    )
    
    # Add reference lines
    fig.add_hline(y=0.8, line_dash="dash", line_color=COLORS['secondary'], 
                 annotation_text="High Correlation", annotation_font_color=COLORS['text'])
    fig.add_hline(y=0, line_dash="dot", line_color=COLORS['text'])
    fig.add_hline(y=-0.8, line_dash="dash", line_color=COLORS['danger'],
                 annotation_text="Negative Correlation", annotation_font_color=COLORS['text'])
    
    fig.update_layout(
        title=dict(
            text=f'Rolling Correlation: {s1.upper()} vs {s2.upper()} ({window} periods)',
            font=dict(color=COLORS['text'], size=18)
        ),
        xaxis_title="Time",
        yaxis_title="Correlation",
        height=400,
        **CHART_TEMPLATE['layout']
    )
    
    return fig
