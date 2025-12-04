"""
EMA (Exponential Moving Average) crossover trading strategy.
"""

import pandas as pd
from typing import Dict, Any
from .base_strategy import BaseStrategy, SignalType
from ..utils.indicators import calculate_ema


class EMACrossStrategy(BaseStrategy):
    """EMA crossover-based trading strategy."""
    
    def __init__(self, parameters: Dict[str, Any]):
        """
        Initialize EMA crossover strategy.
        
        Args:
            parameters: Strategy parameters including:
                - fast_ema: Fast EMA period (default: 9)
                - slow_ema: Slow EMA period (default: 21)
                - trend_ema: Trend filter EMA period (default: 50, optional)
        """
        super().__init__("EMA Crossover Strategy", parameters)
        
        self.fast_ema = parameters.get('fast_ema', 9)
        self.slow_ema = parameters.get('slow_ema', 21)
        self.trend_ema = parameters.get('trend_ema', 50)
        self.use_trend_filter = parameters.get('use_trend_filter', True)
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate EMA indicators.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with EMA columns added
        """
        df = data.copy()
        
        df['ema_fast'] = calculate_ema(df['close'], period=self.fast_ema)
        df['ema_slow'] = calculate_ema(df['close'], period=self.slow_ema)
        
        if self.use_trend_filter:
            df['ema_trend'] = calculate_ema(df['close'], period=self.trend_ema)
        
        return df
    
    def generate_signal(self, symbol: str, data: pd.DataFrame) -> SignalType:
        """
        Generate trading signal based on EMA crossover.
        
        Strategy logic:
        - BUY when fast EMA crosses above slow EMA (golden cross)
        - SELL when fast EMA crosses below slow EMA (death cross)
        - Optional: Only trade in direction of trend EMA
        
        Args:
            symbol: Trading pair symbol
            data: OHLCV DataFrame
            
        Returns:
            SignalType
        """
        min_periods = max(self.slow_ema, self.trend_ema if self.use_trend_filter else 0) + 10
        if not self.validate_data(data, min_periods=min_periods):
            return SignalType.HOLD
        
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        if len(df) < 2:
            return SignalType.HOLD
        
        # Get current and previous values
        current_fast = df['ema_fast'].iloc[-1]
        current_slow = df['ema_slow'].iloc[-1]
        current_close = df['close'].iloc[-1]
        
        prev_fast = df['ema_fast'].iloc[-2]
        prev_slow = df['ema_slow'].iloc[-2]
        
        # Check for valid values
        if any(pd.isna(x) for x in [current_fast, current_slow, prev_fast, prev_slow]):
            return SignalType.HOLD
        
        # Trend filter
        uptrend = True
        downtrend = True
        
        if self.use_trend_filter:
            current_trend = df['ema_trend'].iloc[-1]
            if pd.notna(current_trend):
                uptrend = current_close > current_trend
                downtrend = current_close < current_trend
        
        # Check if we have an existing position
        position = self.get_position(symbol)
        
        if position:
            # Exit logic
            if position['side'] == 'long':
                # Exit long when fast EMA crosses below slow EMA
                if prev_fast >= prev_slow and current_fast < current_slow:
                    return SignalType.CLOSE_LONG
                # Also exit if trend turns bearish
                if self.use_trend_filter and not uptrend and downtrend:
                    return SignalType.CLOSE_LONG
                    
            elif position['side'] == 'short':
                # Exit short when fast EMA crosses above slow EMA
                if prev_fast <= prev_slow and current_fast > current_slow:
                    return SignalType.CLOSE_SHORT
                # Also exit if trend turns bullish
                if self.use_trend_filter and not downtrend and uptrend:
                    return SignalType.CLOSE_SHORT
        else:
            # Entry logic
            # Buy signal: fast EMA crosses above slow EMA
            if prev_fast < prev_slow and current_fast > current_slow:
                # Check trend filter
                if not self.use_trend_filter or uptrend:
                    return SignalType.BUY
            
            # Sell signal: fast EMA crosses below slow EMA
            if prev_fast > prev_slow and current_fast < current_slow:
                # Check trend filter
                if not self.use_trend_filter or downtrend:
                    return SignalType.SELL
        
        return SignalType.HOLD
