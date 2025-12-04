"""
Strategy combiner for multi-strategy signal aggregation.
"""

from typing import List, Dict
import pandas as pd
from strategies.base_strategy import BaseStrategy, Signal
from strategies.scalping_strategy import ScalpingStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.ema_cross_strategy import EMACrossStrategy
from utils.logger import get_logger

logger = get_logger()


class StrategyCombiner(BaseStrategy):
    """Combines signals from multiple strategies."""
    
    def __init__(self, params=None):
        """Initialize strategy combiner."""
        super().__init__('combined', params)
        
        # Initialize strategies
        self.strategies: Dict[str, BaseStrategy] = {
            'scalping': ScalpingStrategy(),
            'rsi': RSIStrategy(),
            'macd': MACDStrategy(),
            'bollinger': BollingerStrategy(),
            'momentum': MomentumStrategy(),
            'ema_cross': EMACrossStrategy()
        }
        
        # Get weights from params
        self.weights = {
            'scalping': self.get_param('weight_scalping', 1.0),
            'rsi': self.get_param('weight_rsi', 1.5),
            'macd': self.get_param('weight_macd', 1.5),
            'bollinger': self.get_param('weight_bollinger', 1.0),
            'momentum': self.get_param('weight_momentum', 1.0),
            'ema_cross': self.get_param('weight_ema_cross', 1.0)
        }
        
        logger.info(f"Strategy Combiner initialized with weights: {self.weights}")
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """
        Generate combined signal from multiple strategies.
        
        Args:
            df: DataFrame with OHLCV data and indicators
            
        Returns:
            Combined Signal object
        """
        # Get minimum signals required
        min_signals = self.get_param('min_signals', 2)
        
        # Collect signals from all strategies
        signals: List[tuple] = []  # (strategy_name, signal, weight)
        
        for name, strategy in self.strategies.items():
            try:
                signal = strategy.generate_signal(df)
                if not signal.is_neutral():
                    signals.append((name, signal, self.weights[name]))
            except Exception as e:
                logger.error(f"Error getting signal from {name}: {e}")
        
        # Check if we have enough signals
        if len(signals) < min_signals:
            return Signal(
                Signal.NEUTRAL,
                reason=f"Insufficient signals ({len(signals)}/{min_signals})"
            )
        
        # Calculate weighted score
        long_score = 0.0
        short_score = 0.0
        total_weight = 0.0
        reasons = []
        
        for name, signal, weight in signals:
            if signal.is_long():
                long_score += signal.strength * weight
                reasons.append(f"{name}:LONG")
            elif signal.is_short():
                short_score += signal.strength * weight
                reasons.append(f"{name}:SHORT")
            
            total_weight += weight
        
        # Determine final signal
        if long_score > short_score and long_score > 0:
            strength = min(long_score / total_weight, 1.0)
            return Signal(
                Signal.LONG,
                strength=strength,
                reason=f"Combined LONG ({len(signals)} signals: {', '.join(reasons)})"
            )
        elif short_score > long_score and short_score > 0:
            strength = min(short_score / total_weight, 1.0)
            return Signal(
                Signal.SHORT,
                strength=strength,
                reason=f"Combined SHORT ({len(signals)} signals: {', '.join(reasons)})"
            )
        else:
            return Signal(
                Signal.NEUTRAL,
                reason=f"Conflicting signals (L:{long_score:.2f} S:{short_score:.2f})"
            )
