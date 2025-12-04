"""
RSI-based reversal strategy.
Trades overbought/oversold conditions with confirmation.
"""

import pandas as pd
from strategies.base_strategy import BaseStrategy, Signal
from utils.logger import get_logger

logger = get_logger()


class RSIStrategy(BaseStrategy):
    """RSI reversal trading strategy."""
    
    def __init__(self, params=None):
        """Initialize RSI strategy."""
        super().__init__('rsi', params)
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """
        Generate RSI-based signal.
        
        Strategy logic:
        - Long: RSI crosses above oversold level (<30), price starts to rise
        - Short: RSI crosses below overbought level (>70), price starts to fall
        
        Args:
            df: DataFrame with OHLCV data and indicators
            
        Returns:
            Signal object
        """
        # Required columns
        required = ['close', 'rsi']
        
        if not self.validate_dataframe(df, required):
            return Signal(Signal.NEUTRAL, reason="Invalid data")
        
        # Get parameters
        rsi_oversold = self.get_param('rsi_oversold', 30)
        rsi_overbought = self.get_param('rsi_overbought', 70)
        rsi_extreme_oversold = self.get_param('rsi_extreme_oversold', 20)
        rsi_extreme_overbought = self.get_param('rsi_extreme_overbought', 80)
        confirmation_candles = self.get_param('confirmation_candles', 2)
        
        # Ensure we have enough data
        if len(df) < confirmation_candles + 1:
            return Signal(Signal.NEUTRAL, reason="Insufficient data")
        
        # Get latest values
        rsi_current = df['rsi'].iloc[-1]
        rsi_prev = df['rsi'].iloc[-2]
        close_current = df['close'].iloc[-1]
        close_prev = df['close'].iloc[-2]
        
        # Check for NaN values
        if pd.isna([rsi_current, rsi_prev, close_current, close_prev]).any():
            return Signal(Signal.NEUTRAL, reason="Incomplete data")
        
        # Check for extreme oversold condition (strong buy)
        if rsi_current < rsi_extreme_oversold:
            # Wait for reversal confirmation
            if rsi_current > rsi_prev and close_current > close_prev:
                strength = 1.0 - (rsi_current / rsi_extreme_oversold)
                return Signal(
                    Signal.LONG,
                    strength=strength,
                    reason=f"Extreme oversold reversal, RSI={rsi_current:.1f}"
                )
        
        # Check for oversold condition
        elif rsi_prev < rsi_oversold and rsi_current > rsi_oversold:
            # RSI crossed above oversold level
            if close_current > close_prev:
                strength = min((rsi_current - rsi_oversold) / (50 - rsi_oversold), 1.0)
                return Signal(
                    Signal.LONG,
                    strength=strength,
                    reason=f"RSI reversal from oversold, RSI={rsi_current:.1f}"
                )
        
        # Check for extreme overbought condition (strong sell)
        if rsi_current > rsi_extreme_overbought:
            # Wait for reversal confirmation
            if rsi_current < rsi_prev and close_current < close_prev:
                strength = (rsi_current - rsi_extreme_overbought) / (100 - rsi_extreme_overbought)
                return Signal(
                    Signal.SHORT,
                    strength=strength,
                    reason=f"Extreme overbought reversal, RSI={rsi_current:.1f}"
                )
        
        # Check for overbought condition
        elif rsi_prev > rsi_overbought and rsi_current < rsi_overbought:
            # RSI crossed below overbought level
            if close_current < close_prev:
                strength = min((rsi_overbought - rsi_current) / (rsi_overbought - 50), 1.0)
                return Signal(
                    Signal.SHORT,
                    strength=strength,
                    reason=f"RSI reversal from overbought, RSI={rsi_current:.1f}"
                )
        
        return Signal(Signal.NEUTRAL, reason="No RSI signal")
