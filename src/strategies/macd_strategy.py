"""
MACD (Moving Average Convergence Divergence) trading strategy.
"""

import pandas as pd
from typing import Dict, Any
from .base_strategy import BaseStrategy, SignalType
from ..utils.indicators import calculate_macd


class MACDStrategy(BaseStrategy):
    """MACD-based trading strategy."""
    
    def __init__(self, parameters: Dict[str, Any]):
        """
        Initialize MACD strategy.
        
        Args:
            parameters: Strategy parameters including:
                - fast_period: Fast EMA period (default: 12)
                - slow_period: Slow EMA period (default: 26)
                - signal_period: Signal line period (default: 9)
        """
        super().__init__("MACD Strategy", parameters)
        
        self.fast_period = parameters.get('fast_period', 12)
        self.slow_period = parameters.get('slow_period', 26)
        self.signal_period = parameters.get('signal_period', 9)
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MACD indicators.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with MACD columns added
        """
        df = data.copy()
        macd_line, signal_line, histogram = calculate_macd(
            df['close'],
            fast=self.fast_period,
            slow=self.slow_period,
            signal=self.signal_period
        )
        
        df['macd'] = macd_line
        df['macd_signal'] = signal_line
        df['macd_histogram'] = histogram
        
        return df
    
    def generate_signal(self, symbol: str, data: pd.DataFrame) -> SignalType:
        """
        Generate trading signal based on MACD.
        
        Strategy logic:
        - BUY when MACD line crosses above signal line (bullish crossover)
        - SELL when MACD line crosses below signal line (bearish crossover)
        - Additional confirmation from histogram direction
        
        Args:
            symbol: Trading pair symbol
            data: OHLCV DataFrame
            
        Returns:
            SignalType
        """
        min_periods = self.slow_period + self.signal_period + 10
        if not self.validate_data(data, min_periods=min_periods):
            return SignalType.HOLD
        
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        if len(df) < 2:
            return SignalType.HOLD
        
        # Get current and previous values
        current_macd = df['macd'].iloc[-1]
        current_signal = df['macd_signal'].iloc[-1]
        current_hist = df['macd_histogram'].iloc[-1]
        
        prev_macd = df['macd'].iloc[-2]
        prev_signal = df['macd_signal'].iloc[-2]
        prev_hist = df['macd_histogram'].iloc[-2]
        
        # Check for valid values
        if any(pd.isna(x) for x in [current_macd, current_signal, prev_macd, prev_signal]):
            return SignalType.HOLD
        
        # Check if we have an existing position
        position = self.get_position(symbol)
        
        if position:
            # Exit logic
            if position['side'] == 'long':
                # Exit long when MACD crosses below signal
                if prev_macd >= prev_signal and current_macd < current_signal:
                    return SignalType.CLOSE_LONG
                # Also exit if histogram turns negative after being positive
                if prev_hist > 0 and current_hist < 0:
                    return SignalType.CLOSE_LONG
                    
            elif position['side'] == 'short':
                # Exit short when MACD crosses above signal
                if prev_macd <= prev_signal and current_macd > current_signal:
                    return SignalType.CLOSE_SHORT
                # Also exit if histogram turns positive after being negative
                if prev_hist < 0 and current_hist > 0:
                    return SignalType.CLOSE_SHORT
        else:
            # Entry logic
            # Buy signal: MACD crosses above signal line
            if prev_macd < prev_signal and current_macd > current_signal:
                # Confirm with histogram turning positive
                if current_hist > prev_hist:
                    return SignalType.BUY
            
            # Sell signal: MACD crosses below signal line
            if prev_macd > prev_signal and current_macd < current_signal:
                # Confirm with histogram turning negative
                if current_hist < prev_hist:
                    return SignalType.SELL
        
        return SignalType.HOLD
