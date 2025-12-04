"""
RSI (Relative Strength Index) trading strategy.
"""

import pandas as pd
from typing import Dict, Any
from .base_strategy import BaseStrategy, SignalType
from ..utils.indicators import calculate_rsi


class RSIStrategy(BaseStrategy):
    """RSI-based trading strategy."""
    
    def __init__(self, parameters: Dict[str, Any]):
        """
        Initialize RSI strategy.
        
        Args:
            parameters: Strategy parameters including:
                - period: RSI period (default: 14)
                - oversold: Oversold threshold (default: 30)
                - overbought: Overbought threshold (default: 70)
        """
        super().__init__("RSI Strategy", parameters)
        
        self.period = parameters.get('period', 14)
        self.oversold = parameters.get('oversold', 30)
        self.overbought = parameters.get('overbought', 70)
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI indicator.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with RSI column added
        """
        df = data.copy()
        df['rsi'] = calculate_rsi(df['close'], period=self.period)
        return df
    
    def generate_signal(self, symbol: str, data: pd.DataFrame) -> SignalType:
        """
        Generate trading signal based on RSI.
        
        Strategy logic:
        - BUY when RSI crosses above oversold level (bullish reversal)
        - SELL when RSI crosses below overbought level (bearish reversal)
        - CLOSE_LONG when RSI reaches overbought
        - CLOSE_SHORT when RSI reaches oversold
        
        Args:
            symbol: Trading pair symbol
            data: OHLCV DataFrame
            
        Returns:
            SignalType
        """
        if not self.validate_data(data, min_periods=self.period + 10):
            return SignalType.HOLD
        
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        if len(df) < 2:
            return SignalType.HOLD
        
        # Get current and previous RSI values
        current_rsi = df['rsi'].iloc[-1]
        prev_rsi = df['rsi'].iloc[-2]
        
        # Check if we have valid RSI values
        if pd.isna(current_rsi) or pd.isna(prev_rsi):
            return SignalType.HOLD
        
        # Check if we have an existing position
        position = self.get_position(symbol)
        
        if position:
            # Exit logic
            if position['side'] == 'long':
                # Exit long when RSI reaches overbought or crosses below it
                if current_rsi >= self.overbought or (prev_rsi > self.overbought and current_rsi < self.overbought):
                    return SignalType.CLOSE_LONG
            elif position['side'] == 'short':
                # Exit short when RSI reaches oversold or crosses above it
                if current_rsi <= self.oversold or (prev_rsi < self.oversold and current_rsi > self.oversold):
                    return SignalType.CLOSE_SHORT
        else:
            # Entry logic
            # Buy signal: RSI crosses above oversold level
            if prev_rsi <= self.oversold and current_rsi > self.oversold:
                return SignalType.BUY
            
            # Sell signal: RSI crosses below overbought level
            if prev_rsi >= self.overbought and current_rsi < self.overbought:
                return SignalType.SELL
        
        return SignalType.HOLD
