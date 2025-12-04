"""
Strategy Selector Module

Selects the optimal trading strategy based on current market conditions.
Uses a scoring system to match strategies with market conditions.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .market_analyzer import MarketCondition


@dataclass
class StrategyScore:
    """
    Strategy scoring result.
    
    Attributes:
        name: Strategy name
        score: Compatibility score (0-100)
        reasons: List of reasons for the score
    """
    name: str
    score: float
    reasons: List[str]
    
    def __str__(self):
        return f"{self.name}: {self.score:.1f} points"


class StrategySelector:
    """
    Selects optimal trading strategy based on market conditions.
    
    Uses a rule-based scoring system to match strategies with
    volatility, trend, and volume characteristics.
    """
    
    # Strategy definitions with optimal market conditions
    STRATEGY_RULES = {
        'scalping': {
            'volatility': ['MEDIUM', 'HIGH'],
            'trend': ['RANGING', 'WEAK_UP', 'WEAK_DOWN'],
            'volume': ['NORMAL', 'HIGH'],
            'description': 'Short-term trades in sideways markets'
        },
        'rsi': {
            'volatility': ['LOW', 'MEDIUM'],
            'trend': ['RANGING', 'WEAK_UP', 'WEAK_DOWN'],
            'volume': ['LOW', 'NORMAL', 'HIGH'],  # Any volume
            'description': 'Mean reversion in ranging/weak trend markets'
        },
        'macd': {
            'volatility': ['MEDIUM', 'HIGH'],
            'trend': ['STRONG_UP', 'STRONG_DOWN'],
            'volume': ['HIGH'],
            'description': 'Trend following in strong trends'
        },
        'bollinger': {
            'volatility': ['HIGH'],
            'trend': ['RANGING', 'WEAK_UP', 'WEAK_DOWN', 'STRONG_UP', 'STRONG_DOWN'],  # Any
            'volume': ['HIGH'],
            'description': 'Breakout/bounce plays in high volatility'
        },
        'momentum': {
            'volatility': ['HIGH'],
            'trend': ['STRONG_UP', 'STRONG_DOWN'],
            'volume': ['HIGH'],
            'description': 'Ride strong trends with high volatility'
        },
        'ema_cross': {
            'volatility': ['MEDIUM'],
            'trend': ['WEAK_UP', 'WEAK_DOWN', 'STRONG_UP', 'STRONG_DOWN'],
            'volume': ['NORMAL', 'HIGH'],
            'description': 'Catch trend changes and continuations'
        },
        'combined': {
            'volatility': ['LOW', 'MEDIUM', 'HIGH'],  # Any
            'trend': ['RANGING', 'WEAK_UP', 'WEAK_DOWN', 'STRONG_UP', 'STRONG_DOWN'],  # Any
            'volume': ['LOW', 'NORMAL', 'HIGH'],  # Any
            'description': 'Default balanced strategy for uncertain conditions'
        }
    }
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the StrategySelector.
        
        Args:
            config: Configuration dict with strategy parameters
        """
        self.config = config or {}
        
        # Get configuration
        auto_switching = self.config.get('auto_strategy_switching', {})
        self.score_threshold = auto_switching.get('score_threshold', 70)
        self.strategy_weights = auto_switching.get('strategy_weights', {})
        
        # Set default weights if not provided
        for strategy in self.STRATEGY_RULES.keys():
            if strategy not in self.strategy_weights:
                # Combined strategy has lower priority by default
                self.strategy_weights[strategy] = 0.8 if strategy == 'combined' else 1.0
    
    def select_best(self, market_condition: MarketCondition) -> Tuple[str, float]:
        """
        Select the best strategy for given market conditions.
        
        Args:
            market_condition: Current market condition
            
        Returns:
            Tuple of (strategy_name, score)
        """
        # Score all strategies
        strategy_scores = self.score_all_strategies(market_condition)
        
        # Find the best strategy above threshold
        best_strategy = None
        best_score = 0
        
        for strategy_score in strategy_scores:
            if strategy_score.score > best_score:
                best_score = strategy_score.score
                best_strategy = strategy_score.name
        
        # If no strategy meets threshold, use combined
        if best_score < self.score_threshold:
            return 'combined', self._calculate_strategy_score(
                'combined', market_condition
            )[0]
        
        return best_strategy, best_score
    
    def score_all_strategies(self, market_condition: MarketCondition) -> List[StrategyScore]:
        """
        Score all strategies for the given market condition.
        
        Args:
            market_condition: Current market condition
            
        Returns:
            List of StrategyScore objects, sorted by score (descending)
        """
        scores = []
        
        for strategy_name in self.STRATEGY_RULES.keys():
            score, reasons = self._calculate_strategy_score(strategy_name, market_condition)
            scores.append(StrategyScore(
                name=strategy_name,
                score=score,
                reasons=reasons
            ))
        
        # Sort by score descending
        scores.sort(key=lambda x: x.score, reverse=True)
        return scores
    
    def _calculate_strategy_score(
        self, 
        strategy_name: str, 
        market_condition: MarketCondition
    ) -> Tuple[float, List[str]]:
        """
        Calculate compatibility score for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            market_condition: Current market condition
            
        Returns:
            Tuple of (score, reasons)
        """
        rules = self.STRATEGY_RULES[strategy_name]
        reasons = []
        
        # Base score components
        volatility_match = market_condition.volatility in rules['volatility']
        trend_match = market_condition.trend in rules['trend']
        volume_match = market_condition.volume in rules['volume']
        
        # Calculate score (0-100)
        score = 0
        
        # Volatility component (30 points)
        if volatility_match:
            score += 30
            reasons.append(f"Volatility {market_condition.volatility} matches")
        else:
            # Partial credit for close matches
            if self._is_close_match(
                market_condition.volatility, 
                rules['volatility'],
                ['LOW', 'MEDIUM', 'HIGH']
            ):
                score += 15
                reasons.append(f"Volatility {market_condition.volatility} partially matches")
        
        # Trend component (40 points - most important)
        if trend_match:
            score += 40
            reasons.append(f"Trend {market_condition.trend} matches")
        else:
            # Partial credit for compatible trends
            if self._is_compatible_trend(market_condition.trend, rules['trend']):
                score += 20
                reasons.append(f"Trend {market_condition.trend} compatible")
        
        # Volume component (30 points)
        if volume_match:
            score += 30
            reasons.append(f"Volume {market_condition.volume} matches")
        else:
            # Partial credit for adjacent levels
            if self._is_close_match(
                market_condition.volume,
                rules['volume'],
                ['LOW', 'NORMAL', 'HIGH']
            ):
                score += 15
                reasons.append(f"Volume {market_condition.volume} partially matches")
        
        # Apply strategy weight
        weight = self.strategy_weights.get(strategy_name, 1.0)
        score *= weight
        
        if weight != 1.0:
            reasons.append(f"Weight adjustment: {weight}x")
        
        return score, reasons
    
    def _is_close_match(
        self, 
        value: str, 
        allowed_values: List[str],
        level_order: List[str]
    ) -> bool:
        """
        Check if value is adjacent to any allowed value in the level order.
        
        Args:
            value: Current value
            allowed_values: List of allowed values
            level_order: Order of levels (e.g., ['LOW', 'MEDIUM', 'HIGH'])
            
        Returns:
            True if value is adjacent to an allowed value
        """
        try:
            value_idx = level_order.index(value)
            for allowed in allowed_values:
                allowed_idx = level_order.index(allowed)
                if abs(value_idx - allowed_idx) == 1:
                    return True
        except ValueError:
            pass
        return False
    
    def _is_compatible_trend(self, current_trend: str, allowed_trends: List[str]) -> bool:
        """
        Check if current trend is compatible with allowed trends.
        
        Args:
            current_trend: Current trend level
            allowed_trends: List of allowed trend levels
            
        Returns:
            True if compatible
        """
        # Define trend compatibility groups
        uptrend_group = ['STRONG_UP', 'WEAK_UP']
        downtrend_group = ['STRONG_DOWN', 'WEAK_DOWN']
        
        # Check if current and allowed trends are in same direction
        for allowed in allowed_trends:
            # Same trend
            if current_trend == allowed:
                return True
            # Both uptrends
            if current_trend in uptrend_group and allowed in uptrend_group:
                return True
            # Both downtrends
            if current_trend in downtrend_group and allowed in downtrend_group:
                return True
        
        return False
    
    def get_strategy_info(self, strategy_name: str) -> dict:
        """
        Get information about a strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Dict with strategy information
        """
        if strategy_name not in self.STRATEGY_RULES:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return self.STRATEGY_RULES[strategy_name].copy()
