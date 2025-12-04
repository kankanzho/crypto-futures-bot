"""
Technical indicators calculation module.
Provides common technical analysis indicators for trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
from ta.trend import EMAIndicator, MACD, SMAIndicator
from ta.momentum import RSIIndicator, ROCIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.
    
    Args:
        data: Price data series
        period: EMA period
        
    Returns:
        EMA values
    """
    indicator = EMAIndicator(close=data, window=period)
    return indicator.ema_indicator()


def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average.
    
    Args:
        data: Price data series
        period: SMA period
        
    Returns:
        SMA values
    """
    indicator = SMAIndicator(close=data, window=period)
    return indicator.sma_indicator()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index.
    
    Args:
        data: Price data series
        period: RSI period (default 14)
        
    Returns:
        RSI values (0-100)
    """
    indicator = RSIIndicator(close=data, window=period)
    return indicator.rsi()


def calculate_macd(
    data: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        data: Price data series
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line period (default 9)
        
    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    indicator = MACD(
        close=data,
        window_slow=slow_period,
        window_fast=fast_period,
        window_sign=signal_period
    )
    
    macd_line = indicator.macd()
    signal_line = indicator.macd_signal()
    histogram = indicator.macd_diff()
    
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    data: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        data: Price data series
        period: Moving average period (default 20)
        std_dev: Standard deviation multiplier (default 2.0)
        
    Returns:
        Tuple of (Upper band, Middle band, Lower band)
    """
    indicator = BollingerBands(
        close=data,
        window=period,
        window_dev=std_dev
    )
    
    upper = indicator.bollinger_hband()
    middle = indicator.bollinger_mavg()
    lower = indicator.bollinger_lband()
    
    return upper, middle, lower


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    Calculate Average True Range.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ATR period (default 14)
        
    Returns:
        ATR values
    """
    indicator = AverageTrueRange(
        high=high,
        low=low,
        close=close,
        window=period
    )
    return indicator.average_true_range()


def calculate_roc(data: pd.Series, period: int = 10) -> pd.Series:
    """
    Calculate Rate of Change.
    
    Args:
        data: Price data series
        period: ROC period (default 10)
        
    Returns:
        ROC values (percentage)
    """
    indicator = ROCIndicator(close=data, window=period)
    return indicator.roc()


def calculate_vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    Calculate Volume Weighted Average Price.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        volume: Volume series
        period: VWAP period (default 14)
        
    Returns:
        VWAP values
    """
    indicator = VolumeWeightedAveragePrice(
        high=high,
        low=low,
        close=close,
        volume=volume,
        window=period
    )
    return indicator.volume_weighted_average_price()


def calculate_momentum(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Momentum indicator.
    
    Args:
        data: Price data series
        period: Momentum period (default 14)
        
    Returns:
        Momentum values
    """
    return data.diff(period)


def calculate_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
    smooth_k: int = 3,
    smooth_d: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic Oscillator.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: Stochastic period (default 14)
        smooth_k: %K smoothing (default 3)
        smooth_d: %D smoothing (default 3)
        
    Returns:
        Tuple of (%K, %D)
    """
    # Calculate raw stochastic
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    
    stoch = 100 * (close - lowest_low) / (highest_high - lowest_low)
    
    # Smooth %K
    k_line = stoch.rolling(window=smooth_k).mean()
    
    # Calculate %D (moving average of %K)
    d_line = k_line.rolling(window=smooth_d).mean()
    
    return k_line, d_line


def calculate_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    Calculate Average Directional Index.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ADX period (default 14)
        
    Returns:
        ADX values
    """
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate directional movement
    up_move = high - high.shift()
    down_move = low.shift() - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    # Smooth the values
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * pd.Series(plus_dm).rolling(window=period).mean() / atr
    minus_di = 100 * pd.Series(minus_dm).rolling(window=period).mean() / atr
    
    # Calculate DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx


def detect_divergence(
    price: pd.Series,
    indicator: pd.Series,
    lookback: int = 5
) -> Tuple[bool, bool]:
    """
    Detect bullish and bearish divergences.
    
    Args:
        price: Price data series
        indicator: Indicator data series (e.g., RSI)
        lookback: Number of periods to look back
        
    Returns:
        Tuple of (bullish_divergence, bearish_divergence)
    """
    if len(price) < lookback + 1:
        return False, False
    
    # Get recent values
    recent_price = price.iloc[-lookback:]
    recent_indicator = indicator.iloc[-lookback:]
    
    # Bullish divergence: price makes lower low, indicator makes higher low
    price_lower_low = recent_price.iloc[-1] < recent_price.iloc[0]
    indicator_higher_low = recent_indicator.iloc[-1] > recent_indicator.iloc[0]
    bullish_div = price_lower_low and indicator_higher_low
    
    # Bearish divergence: price makes higher high, indicator makes lower high
    price_higher_high = recent_price.iloc[-1] > recent_price.iloc[0]
    indicator_lower_high = recent_indicator.iloc[-1] < recent_indicator.iloc[0]
    bearish_div = price_higher_high and indicator_lower_high
    
    return bullish_div, bearish_div


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all technical indicators for a dataframe.
    
    Args:
        df: DataFrame with OHLCV data (must have columns: open, high, low, close, volume)
        
    Returns:
        DataFrame with all indicators added
    """
    result = df.copy()
    
    # Moving Averages
    result['ema_5'] = calculate_ema(df['close'], 5)
    result['ema_9'] = calculate_ema(df['close'], 9)
    result['ema_13'] = calculate_ema(df['close'], 13)
    result['ema_21'] = calculate_ema(df['close'], 21)
    result['ema_50'] = calculate_ema(df['close'], 50)
    result['sma_20'] = calculate_sma(df['close'], 20)
    
    # RSI
    result['rsi'] = calculate_rsi(df['close'], 14)
    
    # MACD
    macd, signal, hist = calculate_macd(df['close'])
    result['macd'] = macd
    result['macd_signal'] = signal
    result['macd_hist'] = hist
    
    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df['close'])
    result['bb_upper'] = bb_upper
    result['bb_middle'] = bb_middle
    result['bb_lower'] = bb_lower
    
    # ATR
    result['atr'] = calculate_atr(df['high'], df['low'], df['close'])
    
    # ROC
    result['roc'] = calculate_roc(df['close'], 10)
    
    # Momentum
    result['momentum'] = calculate_momentum(df['close'], 14)
    
    # Stochastic
    stoch_k, stoch_d = calculate_stochastic(df['high'], df['low'], df['close'])
    result['stoch_k'] = stoch_k
    result['stoch_d'] = stoch_d
    
    # Volume MA
    result['volume_ma'] = df['volume'].rolling(window=20).mean()
    
    return result
