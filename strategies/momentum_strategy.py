"""Momentum strategy based on rate of change."""
import pandas as pd
from strategies.base_strategy import BaseStrategy, Signal

class MomentumStrategy(BaseStrategy):
    """Momentum trading strategy."""
    
    def __init__(self, params=None):
        super().__init__('momentum', params)
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        required = ['close', 'roc', 'volume', 'volume_ma']
        if not self.validate_dataframe(df, required):
            return Signal(Signal.NEUTRAL, reason="Invalid data")
        
        roc = df['roc'].iloc[-1]
        prev_roc = df['roc'].iloc[-2]
        volume = df['volume'].iloc[-1]
        volume_ma = df['volume_ma'].iloc[-1]
        
        if pd.isna([roc, prev_roc, volume, volume_ma]).any():
            return Signal(Signal.NEUTRAL, reason="Incomplete data")
        
        roc_threshold = self.get_param('roc_threshold', 2.0)
        volume_threshold = self.get_param('volume_threshold', 1.5)
        
        volume_high = volume > (volume_ma * volume_threshold)
        
        # Long: Strong positive momentum
        if roc > roc_threshold and prev_roc <= roc_threshold and volume_high:
            strength = min(roc / (roc_threshold * 3), 1.0)
            return Signal(Signal.LONG, strength=strength, reason=f"Strong momentum, ROC={roc:.2f}")
        
        # Short: Strong negative momentum
        if roc < -roc_threshold and prev_roc >= -roc_threshold and volume_high:
            strength = min(abs(roc) / (roc_threshold * 3), 1.0)
            return Signal(Signal.SHORT, strength=strength, reason=f"Negative momentum, ROC={roc:.2f}")
        
        return Signal(Signal.NEUTRAL, reason="No momentum signal")
