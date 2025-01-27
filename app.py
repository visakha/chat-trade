from typing import Dict, List, Optional, Union, Any, Tuple
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import requests
import json
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import datetime
from plotly.subplots import make_subplots

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)

# Custom Technical Indicator Functions
def calculate_sma(data: pd.Series, window: int) -> pd.Series:
    """Calculate Simple Moving Average
    
    Args:
        data: Price series data
        window: Window size for moving average
    
    Returns:
        Series containing SMA values
    """
    return data.rolling(window=window).mean()

def calculate_ema(data: pd.Series, window: int) -> pd.Series:
    """Calculate Exponential Moving Average
    
    Args:
        data: Price series data
        window: Window size for moving average
    
    Returns:
        Series containing EMA values
    """
    return data.ewm(span=window, adjust=False).mean()

def calculate_rsi(data: pd.Series, window: int = 14) -> pd.Series:
    """Calculate Relative Strength Index
    
    Args:
        data: Price series data
        window: Window size for RSI calculation, defaults to 14
    
    Returns:
        Series containing RSI values
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD (Moving Average Convergence Divergence)
    
    Args:
        data: Price series data
        fast_period: Fast EMA period, defaults to 12
        slow_period: Slow EMA period, defaults to 26
        signal_period: Signal line period, defaults to 9
    
    Returns:
        Tuple containing (MACD line, Signal line, MACD histogram)
    """
    fast_ema = calculate_ema(data, fast_period)
    slow_ema = calculate_ema(data, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = calculate_ema(macd_line, signal_period)
    macd_histogram = macd_line - signal_line
    return macd_line, signal_line, macd_histogram

def calculate_bollinger_bands(data: pd.Series, window: int = 20, num_std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands
    
    Args:
        data: Price series data
        window: Window size for moving average, defaults to 20
        num_std: Number of standard deviations, defaults to 2
    
    Returns:
        Tuple containing (Upper band, Middle band, Lower band)
    """
    middle_band = calculate_sma(data, window)
    std = data.rolling(window=window).std()
    upper_band = middle_band + (std * num_std)
    lower_band = middle_band - (std * num_std)
    return upper_band, middle_band, lower_band

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculate Volume Weighted Average Price (VWAP)
    
    Args:
        df: DataFrame containing 'High', 'Low', 'Close' and 'Volume' columns
    
    Returns:
        Series containing VWAP values
    """
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vwap = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
    return vwap

def calculate_vwap_crossover(df: pd.DataFrame, sma_period: int = 9) -> Tuple[pd.Series, pd.Series]:
    """Calculate crossover signals between SMA and VWAP
    
    Args:
        df: DataFrame containing price and volume data
        sma_period: Period for SMA calculation, defaults to 9
    
    Returns:
        Tuple containing (buy signals, sell signals) where each signal is a Series
        with index matching df and values being the price at signal points
    """
    vwap = calculate_vwap(df)
    sma = calculate_sma(df['Close'], sma_period)
    
    # Previous day's values
    prev_sma = sma.shift(1)
    prev_vwap = vwap.shift(1)
    
    # Buy signal: SMA crosses above VWAP
    buy_signal = (sma > vwap) & (prev_sma <= prev_vwap)
    
    # Sell signal: SMA crosses below VWAP
    sell_signal = (sma < vwap) & (prev_sma >= prev_vwap)
    
    # Return Series with price values where signals occur, NaN elsewhere
    buy_prices = pd.Series(index=df.index, data=None)
    buy_prices[buy_signal] = df['Close'][buy_signal]
    
    sell_prices = pd.Series(index=df.index, data=None)
    sell_prices[sell_signal] = df['Close'][sell_signal]
    
    return buy_prices, sell_prices

def fetch_stock_data(symbol: str, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> pd.DataFrame:
    """Fetch stock data from Yahoo Finance
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        start_date: Start date for data fetch
        end_date: End date for data fetch
    
    Returns:
        DataFrame containing OHLCV data
    
    Raises:
        ValueError: If data cannot be fetched or is invalid
        requests.RequestException: If there's a network error
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    
    headers: Dict[str, str] = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    params: Dict[str, Any] = {
        "period1": int(pd.Timestamp(start_date).timestamp()),
        "period2": int(pd.Timestamp(end_date).timestamp()),
        "interval": "1d",
        "includePrePost": False,
        "events": "div,splits"
    }
    
    print(f"\nDebug: Fetching data for {symbol}")
    print(f"Debug: URL: {url}")
    print(f"Debug: Parameters: {params}")
    
    try:
        response = http.get(url, headers=headers, params=params)
        print(f"Debug: Response status code: {response.status_code}")
        
        if response.status_code == 429:
            print("Debug: Rate limited, waiting 5 seconds before retry...")
            time.sleep(5)
            response = http.get(url, headers=headers, params=params)
            print(f"Debug: Retry response status code: {response.status_code}")
        
        data = response.json()
        print(f"Debug: Response data structure: {list(data.keys())}")
        
        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]
            df = pd.DataFrame({
                'Date': pd.to_datetime(result['timestamp'], unit='s'),
                'Open': result['indicators']['quote'][0]['open'],
                'High': result['indicators']['quote'][0]['high'],
                'Low': result['indicators']['quote'][0]['low'],
                'Close': result['indicators']['quote'][0]['close'],
                'Volume': result['indicators']['quote'][0]['volume']
            })
            df.set_index('Date', inplace=True)
            
            print("\nDebug: First 5 rows of the dataframe:")
            print(df.head())
            return df
        else:
            error_msg = f"Could not fetch data for {symbol}. Response structure is invalid."
            print(f"Debug: Error: {error_msg}")
            print(f"Debug: Full response: {json.dumps(data, indent=2)}")
            raise ValueError(error_msg)
    except Exception as e:
        print(f"Debug: Exception occurred: {str(e)}")
        if hasattr(response, 'text'):
            print(f"Debug: Full response text: {response.text}")
        raise

# Initialize the Dash app
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    assets_folder='assets'
)

server = app.server

# Define the sidebar
sidebar = html.Div(
    [
        html.Div(
            [
                html.H2("Stock Analysis", className="sidebar-header"),
            ],
            className="sidebar-header",
        ),
        html.Ul(
            [
                html.Li(
                    dcc.Link(
                        "Technical Analysis",
                        href="/technical-analysis",
                        className="nav-item active"
                    ),
                    className="nav-item"
                ),
                html.Li(
                    dcc.Link(
                        "Portfolio Analysis",
                        href="/portfolio",
                        className="nav-item"
                    ),
                    className="nav-item"
                ),
                html.Li(
                    dcc.Link(
                        "Market Overview",
                        href="/market",
                        className="nav-item"
                    ),
                    className="nav-item"
                ),
            ],
            className="sidebar-nav",
        ),
    ],
    className="sidebar",
)

# Technical Analysis Layout
technical_analysis_layout = html.Div(
    [
        html.Div(
            [
                html.H3("Stock Technical Analysis", style={'margin-bottom': '20px'}),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Stock Symbol:", className="control-label"),
                                dcc.Input(
                                    id='symbol-input',
                                    value='AAPL',
                                    type='text',
                                    className="input-field"
                                ),
                            ],
                            className="control-group"
                        ),
                        html.Div(
                            [
                                html.Label("Date Range:", className="control-label"),
                                dcc.DatePickerRange(
                                    id='date-range',
                                    min_date_allowed=pd.Timestamp.now().date() - pd.Timedelta(days=365*2),
                                    max_date_allowed=pd.Timestamp.now().date(),
                                    start_date=pd.Timestamp.now().date() - pd.Timedelta(days=365),
                                    end_date=pd.Timestamp.now().date(),
                                    className="date-picker"
                                ),
                            ],
                            className="control-group"
                        ),
                        html.Div(
                            [
                                html.Label("Technical Indicators:", className="control-label"),
                                dcc.Checklist(
                                    id='indicators-checklist',
                                    options=[
                                        {'label': 'SMA 50', 'value': 'sma50'},
                                        {'label': 'SMA 200', 'value': 'sma200'},
                                        {'label': 'EMA 50', 'value': 'ema50'},
                                        {'label': 'EMA 200', 'value': 'ema200'},
                                        {'label': 'RSI', 'value': 'rsi'},
                                        {'label': 'MACD', 'value': 'macd'},
                                        {'label': 'Bollinger Bands', 'value': 'bbands'},
                                        {'label': 'VWAP', 'value': 'vwap'}
                                    ],
                                    value=['sma50', 'sma200'],
                                    className="checklist-container"
                                ),
                            ],
                            className="control-group"
                        ),
                    ],
                    className="controls-container"
                ),
                html.Div(
                    dcc.Graph(id='stock-chart'),
                    className="chart-container"
                ),
            ],
            className="content"
        ),
    ],
    className="main-content"
)

# Portfolio Analysis Layout (placeholder)
portfolio_layout = html.Div(
    [
        html.H3("Portfolio Analysis"),
        html.P("Portfolio analysis features coming soon..."),
    ],
    className="content"
)

# Market Overview Layout (placeholder)
market_layout = html.Div(
    [
        html.H3("Market Overview"),
        html.P("Market overview features coming soon..."),
    ],
    className="content"
)

# Main app layout
app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        html.Div(
            [
                sidebar,
                html.Div(id='page-content', className="content")
            ],
            className="main-container"
        ),
    ]
)

# Update page content based on URL
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname: str) -> html.Div:
    if pathname == '/portfolio':
        return portfolio_layout
    elif pathname == '/market':
        return market_layout
    else:  # Default to technical analysis
        return technical_analysis_layout

# Update chart based on input values
@app.callback(
    Output('stock-chart', 'figure'),
    [Input('symbol-input', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('indicators-checklist', 'value')]
)
def update_chart(symbol: str, start_date: str, end_date: str, indicators: List[str]) -> Dict[str, Any]:
    """Update the stock chart with selected indicators
    
    Args:
        symbol: Stock symbol
        start_date: Start date string
        end_date: End date string
        indicators: List of selected technical indicators
    
    Returns:
        Plotly figure dictionary
    """
    # Fetch stock data
    try:
        df = fetch_stock_data(symbol, start_date, end_date)
    except Exception as e:
        return go.Figure(layout=go.Layout(title=f"Error: {str(e)}"))
    
    # Create base candlestick chart
    candlestick = go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    )
    
    # Initialize traces list with candlestick
    traces = [candlestick]
    
    # Add selected technical indicators
    for indicator in indicators:
        if indicator == 'sma50':
            # 50-day Simple Moving Average
            sma_50 = calculate_sma(df['Close'], 50)
            traces.append(
                go.Scatter(x=df.index, y=sma_50, mode='lines', name='SMA 50', line=dict(color='blue', width=2))
            )
        
        if indicator == 'sma200':
            # 200-day Simple Moving Average
            sma_200 = calculate_sma(df['Close'], 200)
            traces.append(
                go.Scatter(x=df.index, y=sma_200, mode='lines', name='SMA 200', line=dict(color='red', width=2))
            )
        
        if indicator == 'ema50':
            # 50-day Exponential Moving Average
            ema_50 = calculate_ema(df['Close'], 50)
            traces.append(
                go.Scatter(x=df.index, y=ema_50, mode='lines', name='EMA 50', line=dict(color='green', width=2))
            )
        
        if indicator == 'ema200':
            # 200-day Exponential Moving Average
            ema_200 = calculate_ema(df['Close'], 200)
            traces.append(
                go.Scatter(x=df.index, y=ema_200, mode='lines', name='EMA 200', line=dict(color='purple', width=2))
            )
        
        if indicator == 'rsi':
            # Relative Strength Index
            rsi = calculate_rsi(df['Close'])
            traces.append(
                go.Scatter(x=df.index, y=rsi, mode='lines', name='RSI', line=dict(color='orange', width=2))
            )
        
        if indicator == 'macd':
            # MACD
            macd, signal = calculate_macd(df['Close'])
            traces.extend([
                go.Scatter(x=df.index, y=macd, mode='lines', name='MACD', line=dict(color='blue', width=2)),
                go.Scatter(x=df.index, y=signal, mode='lines', name='Signal', line=dict(color='red', width=2))
            ])
        
        if indicator == 'bbands':
            # Bollinger Bands
            upper, middle, lower = calculate_bollinger_bands(df['Close'])
            traces.extend([
                go.Scatter(x=df.index, y=upper, mode='lines', name='BB Upper',
                         line=dict(color='gray', width=1, dash='dash')),
                go.Scatter(x=df.index, y=middle, mode='lines', name='BB Middle',
                         line=dict(color='gray', width=1)),
                go.Scatter(x=df.index, y=lower, mode='lines', name='BB Lower',
                         line=dict(color='gray', width=1, dash='dash'))
            ])
            
        if indicator == 'vwap':
            # VWAP
            vwap = calculate_vwap(df)
            traces.append(
                go.Scatter(x=df.index, y=vwap, mode='lines', name='VWAP', line=dict(color='magenta', width=2))
            )
            
            # Add SMA(9) when VWAP is enabled
            sma9 = calculate_sma(df['Close'], 9)
            traces.append(
                go.Scatter(x=df.index, y=sma9, name='SMA 9', line=dict(color='cyan', width=2))
            )
            
            # Calculate and add crossover signals
            buy_signals, sell_signals = calculate_vwap_crossover(df)
            
            # Add buy signals
            traces.append(
                go.Scatter(
                    x=buy_signals.dropna().index,
                    y=buy_signals.dropna(),
                    mode='markers',
                    name='Buy Signal',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color='green',
                        line=dict(width=2)
                    )
                )
            )
            
            # Add sell signals
            traces.append(
                go.Scatter(
                    x=sell_signals.dropna().index,
                    y=sell_signals.dropna(),
                    mode='markers',
                    name='Sell Signal',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color='red',
                        line=dict(width=2)
                    )
                )
            )

    # Create the figure with subplots if needed
    if 'rsi' in indicators or 'macd' in indicators:
        fig = make_subplots(
            rows=3 if 'macd' in indicators and 'rsi' in indicators else 2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2] if 'macd' in indicators and 'rsi' in indicators else [0.7, 0.3]
        )
        
        # Add main price chart and indicators
        for trace in traces:
            if trace.name in ['RSI']:
                fig.add_trace(trace, row=2, col=1)
            elif trace.name in ['MACD', 'Signal']:
                fig.add_trace(trace, row=3 if 'rsi' in indicators else 2, col=1)
            else:
                fig.add_trace(trace, row=1, col=1)
        
        # Update layout
        fig.update_layout(
            title=f'{symbol} Stock Analysis',
            height=800,
            showlegend=True,
            template='plotly_dark'
        )
        
        # Update y-axes titles
        fig.update_yaxes(title_text="Price", row=1, col=1)
        if 'rsi' in indicators:
            fig.update_yaxes(title_text="RSI", row=2, col=1)
        if 'macd' in indicators:
            fig.update_yaxes(title_text="MACD", row=3 if 'rsi' in indicators else 2, col=1)
    
    else:
        # Create a single plot without subplots
        fig = go.Figure(data=traces)
        fig.update_layout(
            title=f'{symbol} Stock Analysis',
            yaxis_title='Price',
            template='plotly_dark',
            height=600,
            showlegend=True
        )
    
    # Common layout updates
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
