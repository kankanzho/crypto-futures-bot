"""
Scalping strategy optimized for short-term trades.
Uses EMA crossovers, RSI, and volume confirmation.
"""

import pandas as pd
from strategies.base_strategy import BaseStrategy, Signal
from utils.logger import get_logger

logger = get_logger()


class ScalpingStrategy(BaseStrategy):
    """Scalping strategy for 1-minute trades."""
    
    def __init__(self, params=None):
        """Initialize scalping strategy."""
        super().__init__('scalping', params)
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """
        Generate scalping signal.
        
        Strategy logic:
        - Long: Fast EMA crosses above slow EMA, RSI > 30, volume increasing
        - Short: Fast EMA crosses below slow EMA, RSI < 70, volume increasing
        
        Args:
            df: DataFrame with OHLCV data and indicators
            
        Returns:
            Signal object
        """
        # Required columns
        required = ['close', 'ema_5', 'ema_13', 'rsi', 'volume', 'volume_ma']
        
        if not self.validate_dataframe(df, required):
            return Signal(Signal.NEUTRAL, reason="Invalid data")
        
        # Get latest values
        fast_ema = df['ema_5'].iloc[-1]
        slow_ema = df['ema_13'].iloc[-1]
        prev_fast_ema = df['ema_5'].iloc[-2]
        prev_slow_ema = df['ema_13'].iloc[-2]
        rsi = df['rsi'].iloc[-1]
        volume = df['volume'].iloc[-1]
        volume_ma = df['volume_ma'].iloc[-1]
        
        # Check for NaN values
        if pd.isna([fast_ema, slow_ema, prev_fast_ema, prev_slow_ema, rsi, volume, volume_ma]).any():
            return Signal(Signal.NEUTRAL, reason="Incomplete data")
        
        # Get parameters
        rsi_oversold = self.get_param('rsi_oversold', 30)
        rsi_overbought = self.get_param('rsi_overbought', 70)
        volume_threshold = self.get_param('volume_threshold', 1.5)
        
        # Check volume condition
        volume_increasing = volume > (volume_ma * volume_threshold)
        
        # Check for EMA crossover
        bullish_cross = (fast_ema > slow_ema) and (prev_fast_ema <= prev_slow_ema)
        bearish_cross = (fast_ema < slow_ema) and (prev_fast_ema >= prev_slow_ema)
        
        # Long signal
        if bullish_cross and rsi > rsi_oversold and volume_increasing:
            strength = min((rsi - rsi_oversold) / (50 - rsi_oversold), 1.0)
            return Signal(
                Signal.LONG,
                strength=strength,
                reason=f"Bullish EMA cross, RSI={rsi:.1f}, Volume spike"
            )
        
        # Short signal
        if bearish_cross and rsi < rsi_overbought and volume_increasing:
            strength = min((rsi_overbought - rsi) / (rsi_overbought - 50), 1.0)
            return Signal(
                Signal.SHORT,
                strength=strength,
                reason=f"Bearish EMA cross, RSI={rsi:.1f}, Volume spike"
            )
        
        return Signal(Signal.NEUTRAL, reason="No signal")
