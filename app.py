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
from indicators import (
    calculate_sma, 
    calculate_ema, 
    calculate_rsi, 
    calculate_macd, 
    calculate_bollinger_bands, 
    calculate_vwap, 
    calculate_vwap_crossover
)

import os
from logger_config import setup_logging, logger

# Import layouts
from layouts.sidebar import sidebar
from layouts.technical_analysis import technical_analysis_layout
from layouts.portfolio import portfolio_layout
from layouts.market import market_layout

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)

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
    
    logger.debug(f"Fetching data for {symbol}")
    logger.debug(f"URL: {url}")
    logger.debug(f"Parameters: {params}")
    
    try:
        response = http.get(url, headers=headers, params=params)
        logger.debug(f"Response status code: {response.status_code}")
        
        if response.status_code == 429:
            logger.warning("Rate limited, waiting 5 seconds before retry...")
            time.sleep(5)
            response = http.get(url, headers=headers, params=params)
            logger.debug(f"Retry response status code: {response.status_code}")
        
        data = response.json()
        logger.debug(f"Response data structure: {list(data.keys())}")
        
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
            
            logger.debug("First 5 rows of the dataframe:")
            logger.debug(df.head())
            return df
        else:
            error_msg = f"Could not fetch data for {symbol}. Response structure is invalid."
            logger.error(error_msg)
            logger.error(f"Full response: {json.dumps(data, indent=2)}")
            raise ValueError(error_msg)
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        if hasattr(response, 'text'):
            logger.error(f"Full response text: {response.text}")
        raise

def create_candlestick_trace(df: pd.DataFrame) -> go.Candlestick:
    """Create a candlestick trace from the DataFrame"""
    return go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    )

def add_technical_indicators(df: pd.DataFrame, indicators: List[str]) -> List[go.Scatter]:
    """Add technical indicators based on selected options"""
    indicator_traces = []

    # SMA Indicators
    if 'sma50' in indicators:
        sma_50 = calculate_sma(df['Close'], window=50)
        indicator_traces.append(go.Scatter(x=df.index, y=sma_50, mode='lines', name='SMA 50', line=dict(color='blue', width=2)))
    
    if 'sma200' in indicators:
        sma_200 = calculate_sma(df['Close'], window=200)
        indicator_traces.append(go.Scatter(x=df.index, y=sma_200, mode='lines', name='SMA 200', line=dict(color='red', width=2)))
    
    # EMA Indicators
    if 'ema50' in indicators:
        ema_50 = calculate_ema(df['Close'], window=50)
        indicator_traces.append(go.Scatter(x=df.index, y=ema_50, mode='lines', name='EMA 50', line=dict(color='green', width=2)))
    
    if 'ema200' in indicators:
        ema_200 = calculate_ema(df['Close'], window=200)
        indicator_traces.append(go.Scatter(x=df.index, y=ema_200, mode='lines', name='EMA 200', line=dict(color='purple', width=2)))
    
    # RSI
    if 'rsi' in indicators:
        rsi = calculate_rsi(df['Close'])
        indicator_traces.append(go.Scatter(x=df.index, y=rsi, mode='lines', name='RSI', line=dict(color='orange', width=2)))
    
    # MACD
    if 'macd' in indicators:
        macd_line, signal_line, _ = calculate_macd(df['Close'])
        indicator_traces.extend([
            go.Scatter(x=df.index, y=macd_line, mode='lines', name='MACD Line', line=dict(color='blue', width=2)),
            go.Scatter(x=df.index, y=signal_line, mode='lines', name='Signal Line', line=dict(color='red', width=2))
        ])
    
    # Bollinger Bands
    if 'bbands' in indicators:
        upper_band, middle_band, lower_band = calculate_bollinger_bands(df['Close'])
        indicator_traces.extend([
            go.Scatter(x=df.index, y=upper_band, mode='lines', name='Upper BB', line=dict(color='green', width=1, dash='dot')),
            go.Scatter(x=df.index, y=middle_band, mode='lines', name='Middle BB', line=dict(color='gray', width=1, dash='dot')),
            go.Scatter(x=df.index, y=lower_band, mode='lines', name='Lower BB', line=dict(color='green', width=1, dash='dot'))
        ])
    
    # VWAP
    if 'vwap' in indicators:
        vwap = calculate_vwap(df)
        indicator_traces.append(go.Scatter(x=df.index, y=vwap, mode='lines', name='VWAP', line=dict(color='brown', width=2)))
    
    return indicator_traces

# Initialize the Dash app
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    assets_folder='assets'
)

server = app.server

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
    """Update the stock chart with selected indicators"""
    try:
        # Fetch stock data
        df = fetch_stock_data(symbol, start_date, end_date)
        
        # Create base traces
        traces = [create_candlestick_trace(df)]
        
        # Add technical indicators
        traces.extend(add_technical_indicators(df, indicators))
        
        # Create figure
        figure = go.Figure(data=traces)
        
        # Customize layout
        figure.update_layout(
            title=f'{symbol} Stock Price and Technical Indicators',
            xaxis_title='Date',
            yaxis_title='Price',
            template='plotly_white'
        )
        
        return figure
    
    except Exception as e:
        return go.Figure(layout=go.Layout(title=f"Error: {str(e)}"))

if __name__ == '__main__':
    app.run_server(debug=True)
