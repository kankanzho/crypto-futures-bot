"""Bollinger Bands breakout strategy."""
import pandas as pd
from strategies.base_strategy import BaseStrategy, Signal

class BollingerStrategy(BaseStrategy):
    """Bollinger Bands trading strategy."""
    
    def __init__(self, params=None):
        super().__init__('bollinger', params)
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        required = ['close', 'bb_upper', 'bb_middle', 'bb_lower']
        if not self.validate_dataframe(df, required):
            return Signal(Signal.NEUTRAL, reason="Invalid data")
        
        close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        bb_upper = df['bb_upper'].iloc[-1]
        bb_lower = df['bb_lower'].iloc[-1]
        bb_middle = df['bb_middle'].iloc[-1]
        
        if pd.isna([close, prev_close, bb_upper, bb_lower, bb_middle]).any():
            return Signal(Signal.NEUTRAL, reason="Incomplete data")
        
        # Long: Price bounces off lower band
        if prev_close <= bb_lower and close > bb_lower:
            strength = (bb_middle - close) / (bb_middle - bb_lower)
            return Signal(Signal.LONG, strength=strength, reason="BB lower band bounce")
        
        # Short: Price bounces off upper band
        if prev_close >= bb_upper and close < bb_upper:
            strength = (close - bb_middle) / (bb_upper - bb_middle)
            return Signal(Signal.SHORT, strength=strength, reason="BB upper band bounce")
        
        return Signal(Signal.NEUTRAL, reason="No BB signal")
