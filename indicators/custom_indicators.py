"""
Custom technical indicators for advanced trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def calculate_support_resistance(
    df: pd.DataFrame,
    lookback: int = 20,
    num_levels: int = 3
) -> Tuple[list, list]:
    """
    Calculate support and resistance levels.
    
    Args:
        df: DataFrame with OHLCV data
        lookback: Number of periods to look back
        num_levels: Number of S/R levels to identify
        
    Returns:
        Tuple of (support_levels, resistance_levels)
    """
    if len(df) < lookback:
        return [], []
    
    recent_high = df['high'].iloc[-lookback:]
    recent_low = df['low'].iloc[-lookback:]
    
    # Find local maxima (resistance)
    resistance_levels = []
    for i in range(1, len(recent_high) - 1):
        if recent_high.iloc[i] > recent_high.iloc[i-1] and recent_high.iloc[i] > recent_high.iloc[i+1]:
            resistance_levels.append(recent_high.iloc[i])
    
    # Find local minima (support)
    support_levels = []
    for i in range(1, len(recent_low) - 1):
        if recent_low.iloc[i] < recent_low.iloc[i-1] and recent_low.iloc[i] < recent_low.iloc[i+1]:
            support_levels.append(recent_low.iloc[i])
    
    # Sort and get top levels
    resistance_levels = sorted(resistance_levels, reverse=True)[:num_levels]
    support_levels = sorted(support_levels)[:num_levels]
    
    return support_levels, resistance_levels


def calculate_trend_strength(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate trend strength indicator.
    
    Args:
        df: DataFrame with OHLCV data
        period: Period for calculation
        
    Returns:
        Trend strength series (-100 to 100)
    """
    # Calculate directional movement
    up_move = df['high'] - df['high'].shift()
    down_move = df['low'].shift() - df['low']
    
    # Positive directional movement
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    # Smooth
    plus_di = pd.Series(plus_dm).rolling(window=period).sum()
    minus_di = pd.Series(minus_dm).rolling(window=period).sum()
    
    # Calculate trend strength
    total = plus_di + minus_di
    trend_strength = np.where(total > 0, 100 * (plus_di - minus_di) / total, 0)
    
    return pd.Series(trend_strength, index=df.index)


def calculate_volatility_ratio(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate volatility ratio.
    
    Args:
        df: DataFrame with OHLCV data
        period: Period for calculation
        
    Returns:
        Volatility ratio series
    """
    # Calculate true range
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift())
    tr3 = abs(df['low'] - df['close'].shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate ATR
    atr = tr.rolling(window=period).mean()
    
    # Calculate price range
    price_range = df['close'].rolling(window=period).std()
    
    # Volatility ratio
    volatility_ratio = atr / price_range
    
    return volatility_ratio


def calculate_volume_profile(
    df: pd.DataFrame,
    num_bins: int = 20
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate volume profile.
    
    Args:
        df: DataFrame with OHLCV data
        num_bins: Number of price bins
        
    Returns:
        Tuple of (price_levels, volume_at_price)
    """
    if len(df) == 0:
        return pd.Series(), pd.Series()
    
    price_min = df['low'].min()
    price_max = df['high'].max()
    
    # Create price bins
    bins = np.linspace(price_min, price_max, num_bins + 1)
    
    # Calculate volume at each price level
    volume_profile = {}
    for i in range(len(bins) - 1):
        price_level = (bins[i] + bins[i+1]) / 2
        mask = (df['close'] >= bins[i]) & (df['close'] < bins[i+1])
        volume_profile[price_level] = df.loc[mask, 'volume'].sum()
    
    price_levels = pd.Series(list(volume_profile.keys()))
    volume_at_price = pd.Series(list(volume_profile.values()))
    
    return price_levels, volume_at_price


def calculate_order_flow_imbalance(df: pd.DataFrame, period: int = 10) -> pd.Series:
    """
    Calculate order flow imbalance indicator.
    
    Args:
        df: DataFrame with OHLCV data
        period: Period for calculation
        
    Returns:
        Order flow imbalance series
    """
    # Estimate buying vs selling pressure
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    price_change = typical_price.diff()
    
    # Positive change = buying pressure, negative = selling pressure
    buying_volume = np.where(price_change > 0, df['volume'], 0)
    selling_volume = np.where(price_change < 0, df['volume'], 0)
    
    # Calculate imbalance
    buy_vol = pd.Series(buying_volume).rolling(window=period).sum()
    sell_vol = pd.Series(selling_volume).rolling(window=period).sum()
    
    total_vol = buy_vol + sell_vol
    imbalance = np.where(total_vol > 0, (buy_vol - sell_vol) / total_vol, 0)
    
    return pd.Series(imbalance, index=df.index)


def calculate_money_flow_index(
    df: pd.DataFrame,
    period: int = 14
) -> pd.Series:
    """
    Calculate Money Flow Index (MFI).
    
    Args:
        df: DataFrame with OHLCV data
        period: Period for calculation
        
    Returns:
        MFI series (0-100)
    """
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    money_flow = typical_price * df['volume']
    
    # Positive and negative money flow
    positive_flow = np.where(typical_price > typical_price.shift(), money_flow, 0)
    negative_flow = np.where(typical_price < typical_price.shift(), money_flow, 0)
    
    # Calculate money ratio
    positive_mf = pd.Series(positive_flow).rolling(window=period).sum()
    negative_mf = pd.Series(negative_flow).rolling(window=period).sum()
    
    money_ratio = positive_mf / negative_mf
    mfi = 100 - (100 / (1 + money_ratio))
    
    return mfi


def calculate_squeeze_momentum(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Squeeze Momentum Indicator (TTM Squeeze).
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Tuple of (squeeze_on, momentum)
    """
    # Bollinger Bands
    bb_period = 20
    bb_std = 2.0
    bb_middle = df['close'].rolling(window=bb_period).mean()
    bb_std_dev = df['close'].rolling(window=bb_period).std()
    bb_upper = bb_middle + (bb_std * bb_std_dev)
    bb_lower = bb_middle - (bb_std * bb_std_dev)
    
    # Keltner Channels
    kc_period = 20
    kc_atr_period = 20
    kc_middle = df['close'].rolling(window=kc_period).mean()
    
    # Calculate ATR
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift())
    tr3 = abs(df['low'] - df['close'].shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=kc_atr_period).mean()
    
    kc_upper = kc_middle + (1.5 * atr)
    kc_lower = kc_middle - (1.5 * atr)
    
    # Squeeze is on when BB is inside KC
    squeeze_on = (bb_upper < kc_upper) & (bb_lower > kc_lower)
    
    # Momentum calculation
    highest = df['high'].rolling(window=kc_period).max()
    lowest = df['low'].rolling(window=kc_period).min()
    mid_line = (highest + lowest) / 2
    momentum = df['close'] - mid_line
    
    return squeeze_on.astype(int), momentum


def calculate_composite_index(df: pd.DataFrame) -> pd.Series:
    """
    Calculate a composite trend index combining multiple indicators.
    
    Args:
        df: DataFrame with OHLCV data (must have RSI, MACD, trend indicators)
        
    Returns:
        Composite index series (-100 to 100)
    """
    scores = []
    
    # RSI score
    if 'rsi' in df.columns:
        rsi_score = (df['rsi'] - 50) * 2  # Scale to -100 to 100
        scores.append(rsi_score)
    
    # MACD score
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        macd_score = np.where(df['macd'] > df['macd_signal'], 50, -50)
        scores.append(pd.Series(macd_score, index=df.index))
    
    # Price vs MA score
    if 'ema_50' in df.columns:
        ma_score = np.where(df['close'] > df['ema_50'], 50, -50)
        scores.append(pd.Series(ma_score, index=df.index))
    
    # Combine scores
    if scores:
        composite = sum(scores) / len(scores)
        return composite
    
    return pd.Series(0, index=df.index)
