"""
Core modules for the crypto futures trading bot.
"""
from .market_analyzer import MarketAnalyzer, MarketCondition
from .strategy_selector import StrategySelector
from .auto_strategy_manager import AutoStrategyManager

__all__ = [
    'MarketAnalyzer',
    'MarketCondition',
    'StrategySelector',
    'AutoStrategyManager',
]
