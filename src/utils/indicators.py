"""
Technical indicators utility module.
Provides commonly used technical indicators for trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        data: Price data series
        period: RSI period
        
    Returns:
        RSI values as pandas Series
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        data: Price data series
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
        
    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        data: Price data series
        period: Moving average period
        std_dev: Number of standard deviations
        
    Returns:
        Tuple of (Upper band, Middle band, Lower band)
    """
    middle_band = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    return upper_band, middle_band, lower_band


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA).
    
    Args:
        data: Price data series
        period: EMA period
        
    Returns:
        EMA values as pandas Series
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average (SMA).
    
    Args:
        data: Price data series
        period: SMA period
        
    Returns:
        SMA values as pandas Series
    """
    return data.rolling(window=period).mean()


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ATR period
        
    Returns:
        ATR values as pandas Series
    """
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                        k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic Oscillator.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        k_period: %K period
        d_period: %D period (smoothing)
        
    Returns:
        Tuple of (%K, %D)
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(window=d_period).mean()
    
    return k, d


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Average Directional Index (ADX).
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ADX period
        
    Returns:
        ADX values as pandas Series
    """
    # Calculate +DM and -DM
    high_diff = high.diff()
    low_diff = -low.diff()
    
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    
    # Calculate ATR
    atr = calculate_atr(high, low, close, period)
    
    # Calculate +DI and -DI
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    # Calculate DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx


def detect_support_resistance(data: pd.Series, window: int = 20, threshold: float = 0.02) -> dict:
    """
    Detect support and resistance levels.
    
    Args:
        data: Price data series
        window: Window for local min/max detection
        threshold: Minimum distance between levels (as percentage)
        
    Returns:
        Dictionary with support and resistance levels
    """
    # Find local minima (support)
    local_min = data.rolling(window=window, center=True).min()
    support_levels = data[data == local_min].values
    
    # Find local maxima (resistance)
    local_max = data.rolling(window=window, center=True).max()
    resistance_levels = data[data == local_max].values
    
    # Remove duplicate levels within threshold
    def remove_duplicates(levels):
        if len(levels) == 0:
            return []
        levels = sorted(levels)
        filtered = [levels[0]]
        for level in levels[1:]:
            if (level - filtered[-1]) / filtered[-1] > threshold:
                filtered.append(level)
        return filtered
    
    return {
        'support': remove_duplicates(support_levels.tolist()),
        'resistance': remove_duplicates(resistance_levels.tolist())
    }


def calculate_volatility(data: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate historical volatility (standard deviation of returns).
    
    Args:
        data: Price data series
        period: Period for volatility calculation
        
    Returns:
        Volatility values as pandas Series
    """
    returns = data.pct_change()
    volatility = returns.rolling(window=period).std() * np.sqrt(period)
    
    return volatility
