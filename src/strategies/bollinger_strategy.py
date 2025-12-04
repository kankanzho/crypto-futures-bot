"""
Bollinger Bands trading strategy.
"""

import pandas as pd
from typing import Dict, Any
from .base_strategy import BaseStrategy, SignalType
from ..utils.indicators import calculate_bollinger_bands


class BollingerStrategy(BaseStrategy):
    """Bollinger Bands-based trading strategy."""
    
    def __init__(self, parameters: Dict[str, Any]):
        """
        Initialize Bollinger Bands strategy.
        
        Args:
            parameters: Strategy parameters including:
                - period: Moving average period (default: 20)
                - std_dev: Number of standard deviations (default: 2.0)
        """
        super().__init__("Bollinger Bands Strategy", parameters)
        
        self.period = parameters.get('period', 20)
        self.std_dev = parameters.get('std_dev', 2.0)
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with Bollinger Bands columns added
        """
        df = data.copy()
        upper, middle, lower = calculate_bollinger_bands(
            df['close'],
            period=self.period,
            std_dev=self.std_dev
        )
        
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        df['bb_width'] = (upper - lower) / middle  # Bandwidth
        
        return df
    
    def generate_signal(self, symbol: str, data: pd.DataFrame) -> SignalType:
        """
        Generate trading signal based on Bollinger Bands.
        
        Strategy logic:
        - BUY when price touches or crosses below lower band (oversold)
        - SELL when price touches or crosses above upper band (overbought)
        - Exit long when price reaches middle band or upper band
        - Exit short when price reaches middle band or lower band
        
        Args:
            symbol: Trading pair symbol
            data: OHLCV DataFrame
            
        Returns:
            SignalType
        """
        min_periods = self.period + 10
        if not self.validate_data(data, min_periods=min_periods):
            return SignalType.HOLD
        
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        if len(df) < 2:
            return SignalType.HOLD
        
        # Get current and previous values
        current_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        
        current_upper = df['bb_upper'].iloc[-1]
        current_middle = df['bb_middle'].iloc[-1]
        current_lower = df['bb_lower'].iloc[-1]
        
        prev_upper = df['bb_upper'].iloc[-2]
        prev_lower = df['bb_lower'].iloc[-2]
        
        # Check for valid values
        if any(pd.isna(x) for x in [current_close, current_upper, current_middle, current_lower]):
            return SignalType.HOLD
        
        # Check if we have an existing position
        position = self.get_position(symbol)
        
        if position:
            # Exit logic
            if position['side'] == 'long':
                # Exit long when price reaches middle band or crosses above upper band
                if current_close >= current_middle:
                    return SignalType.CLOSE_LONG
                # Strong exit signal when crossing upper band
                if prev_close <= prev_upper and current_close > current_upper:
                    return SignalType.CLOSE_LONG
                    
            elif position['side'] == 'short':
                # Exit short when price reaches middle band or crosses below lower band
                if current_close <= current_middle:
                    return SignalType.CLOSE_SHORT
                # Strong exit signal when crossing lower band
                if prev_close >= prev_lower and current_close < current_lower:
                    return SignalType.CLOSE_SHORT
        else:
            # Entry logic
            # Buy signal: price crosses below lower band or bounces from it
            if prev_close >= prev_lower and current_close < current_lower:
                return SignalType.BUY
            # Alternative: price is below lower band and starting to bounce
            if current_close < current_lower and current_close > prev_close:
                return SignalType.BUY
            
            # Sell signal: price crosses above upper band or reverses from it
            if prev_close <= prev_upper and current_close > current_upper:
                return SignalType.SELL
            # Alternative: price is above upper band and starting to reverse
            if current_close > current_upper and current_close < prev_close:
                return SignalType.SELL
        
        return SignalType.HOLD
