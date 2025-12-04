"""Trading strategies package."""

from strategies.base_strategy import BaseStrategy, Signal
from strategies.scalping_strategy import ScalpingStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.ema_cross_strategy import EMACrossStrategy
from strategies.strategy_combiner import StrategyCombiner

__all__ = [
    'BaseStrategy',
    'Signal',
    'ScalpingStrategy',
    'RSIStrategy',
    'MACDStrategy',
    'BollingerStrategy',
    'MomentumStrategy',
    'EMACrossStrategy',
    'StrategyCombiner'
]
