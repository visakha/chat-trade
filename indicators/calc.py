import pandas as pd
import numpy as np
from typing import Tuple

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
    
    # Make two series: one for lower closes and one for higher closes
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    # Calculate the EWMA
    roll_up = up.ewm(com=window-1, adjust=False).mean()
    roll_down = down.ewm(com=window-1, adjust=False).mean()
    
    # Calculate the RSI based on EWMA
    rs = roll_up / roll_down
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
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
    # Calculate the fast and slow exponential moving averages
    fast_ema = data.ewm(span=fast_period, adjust=False).mean()
    slow_ema = data.ewm(span=slow_period, adjust=False).mean()
    
    # Calculate the MACD line
    macd_line = fast_ema - slow_ema
    
    # Calculate the signal line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    
    # Calculate the MACD histogram
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
    # Calculate the middle band (simple moving average)
    middle_band = data.rolling(window=window).mean()
    
    # Calculate the standard deviation
    std_dev = data.rolling(window=window).std()
    
    # Calculate upper and lower bands
    upper_band = middle_band + (std_dev * num_std)
    lower_band = middle_band - (std_dev * num_std)
    
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
    # Calculate SMA and VWAP
    sma = calculate_sma(df['Close'], window=sma_period)
    vwap = calculate_vwap(df)
    
    # Initialize buy and sell signals
    buy_signals = pd.Series(index=df.index, dtype=float)
    sell_signals = pd.Series(index=df.index, dtype=float)
    
    # Detect crossover points
    for i in range(1, len(df)):
        # Buy signal: SMA crosses above VWAP
        if (sma.iloc[i-1] <= vwap.iloc[i-1] and 
            sma.iloc[i] > vwap.iloc[i]):
            buy_signals.iloc[i] = df['Close'].iloc[i]
        
        # Sell signal: SMA crosses below VWAP
        if (sma.iloc[i-1] >= vwap.iloc[i-1] and 
            sma.iloc[i] < vwap.iloc[i]):
            sell_signals.iloc[i] = df['Close'].iloc[i]
    
    return buy_signals, sell_signals
