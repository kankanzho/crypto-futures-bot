"""
MACD crossover strategy.
Trend-following strategy using MACD indicator.
"""

import pandas as pd
from strategies.base_strategy import BaseStrategy, Signal
from utils.logger import get_logger

logger = get_logger()


class MACDStrategy(BaseStrategy):
    """MACD crossover trading strategy."""
    
    def __init__(self, params=None):
        """Initialize MACD strategy."""
        super().__init__('macd', params)
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """
        Generate MACD-based signal.
        
        Strategy logic:
        - Long: MACD line crosses above signal line
        - Short: MACD line crosses below signal line
        
        Args:
            df: DataFrame with OHLCV data and indicators
            
        Returns:
            Signal object
        """
        # Required columns
        required = ['close', 'macd', 'macd_signal', 'macd_hist']
        
        if not self.validate_dataframe(df, required):
            return Signal(Signal.NEUTRAL, reason="Invalid data")
        
        # Get latest values
        macd = df['macd'].iloc[-1]
        macd_signal = df['macd_signal'].iloc[-1]
        macd_hist = df['macd_hist'].iloc[-1]
        prev_macd = df['macd'].iloc[-2]
        prev_macd_signal = df['macd_signal'].iloc[-2]
        
        # Check for NaN values
        if pd.isna([macd, macd_signal, macd_hist, prev_macd, prev_macd_signal]).any():
            return Signal(Signal.NEUTRAL, reason="Incomplete data")
        
        # Get parameters
        use_signal_cross = self.get_param('use_signal_cross', True)
        use_zero_cross = self.get_param('use_zero_cross', False)
        histogram_threshold = self.get_param('histogram_threshold', 0.0)
        
        # Check for crossovers
        bullish_cross = (macd > macd_signal) and (prev_macd <= prev_macd_signal)
        bearish_cross = (macd < macd_signal) and (prev_macd >= prev_macd_signal)
        
        # Long signal
        if use_signal_cross and bullish_cross:
            # Stronger signal if MACD is positive or histogram is large
            strength = 0.5
            if macd > 0:
                strength += 0.3
            if abs(macd_hist) > histogram_threshold:
                strength += 0.2
            
            return Signal(
                Signal.LONG,
                strength=min(strength, 1.0),
                reason=f"MACD bullish cross, MACD={macd:.4f}"
            )
        
        # Short signal
        if use_signal_cross and bearish_cross:
            # Stronger signal if MACD is negative or histogram is large
            strength = 0.5
            if macd < 0:
                strength += 0.3
            if abs(macd_hist) > histogram_threshold:
                strength += 0.2
            
            return Signal(
                Signal.SHORT,
                strength=min(strength, 1.0),
                reason=f"MACD bearish cross, MACD={macd:.4f}"
            )
        
        # Check zero line cross
        if use_zero_cross:
            if macd > 0 and prev_macd <= 0:
                return Signal(
                    Signal.LONG,
                    strength=0.7,
                    reason="MACD crossed above zero"
                )
            
            if macd < 0 and prev_macd >= 0:
                return Signal(
                    Signal.SHORT,
                    strength=0.7,
                    reason="MACD crossed below zero"
                )
        
        return Signal(Signal.NEUTRAL, reason="No MACD signal")
