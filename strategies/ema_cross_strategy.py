"""EMA crossover strategy."""
import pandas as pd
from strategies.base_strategy import BaseStrategy, Signal

class EMACrossStrategy(BaseStrategy):
    """EMA crossover trading strategy."""
    
    def __init__(self, params=None):
        super().__init__('ema_cross', params)
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        required = ['close', 'ema_9', 'ema_21']
        if not self.validate_dataframe(df, required):
            return Signal(Signal.NEUTRAL, reason="Invalid data")
        
        fast_ema = df['ema_9'].iloc[-1]
        slow_ema = df['ema_21'].iloc[-1]
        prev_fast = df['ema_9'].iloc[-2]
        prev_slow = df['ema_21'].iloc[-2]
        
        if pd.isna([fast_ema, slow_ema, prev_fast, prev_slow]).any():
            return Signal(Signal.NEUTRAL, reason="Incomplete data")
        
        use_trend_filter = self.get_param('use_trend_filter', True)
        
        # Check trend if enabled
        if use_trend_filter and 'ema_50' in df.columns:
            trend_ema = df['ema_50'].iloc[-1]
            close = df['close'].iloc[-1]
            if not pd.isna(trend_ema):
                in_uptrend = close > trend_ema
            else:
                in_uptrend = True
        else:
            in_uptrend = True
        
        # Bullish cross
        if fast_ema > slow_ema and prev_fast <= prev_slow:
            if not use_trend_filter or in_uptrend:
                strength = min((fast_ema - slow_ema) / slow_ema * 100, 1.0)
                return Signal(Signal.LONG, strength=strength, reason="EMA bullish cross")
        
        # Bearish cross
        if fast_ema < slow_ema and prev_fast >= prev_slow:
            if not use_trend_filter or not in_uptrend:
                strength = min((slow_ema - fast_ema) / slow_ema * 100, 1.0)
                return Signal(Signal.SHORT, strength=strength, reason="EMA bearish cross")
        
        return Signal(Signal.NEUTRAL, reason="No EMA cross")
