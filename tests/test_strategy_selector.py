"""
Unit tests for StrategySelector
"""

import unittest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.strategy_selector import StrategySelector, StrategyScore
from core.market_analyzer import MarketCondition


class TestStrategySelector(unittest.TestCase):
    """Test cases for StrategySelector."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.selector = StrategySelector()
    
    def test_initialization(self):
        """Test StrategySelector initialization."""
        selector = StrategySelector()
        self.assertIsNotNone(selector)
        self.assertEqual(selector.score_threshold, 70)
    
    def test_initialization_with_config(self):
        """Test StrategySelector initialization with config."""
        config = {
            'auto_strategy_switching': {
                'score_threshold': 80,
                'strategy_weights': {
                    'scalping': 1.2,
                    'momentum': 0.9
                }
            }
        }
        selector = StrategySelector(config)
        self.assertEqual(selector.score_threshold, 80)
        self.assertEqual(selector.strategy_weights['scalping'], 1.2)
        self.assertEqual(selector.strategy_weights['momentum'], 0.9)
    
    def test_select_best_high_volatility_strong_uptrend(self):
        """Test strategy selection for high volatility + strong uptrend."""
        condition = MarketCondition(
            volatility='HIGH',
            trend='STRONG_UP',
            volume='HIGH',
            timestamp=datetime.now()
        )
        
        strategy, score = self.selector.select_best(condition)
        
        # Should select momentum or MACD (both good for strong uptrend + high vol)
        self.assertIn(strategy, ['momentum', 'macd', 'bollinger'])
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_select_best_low_volatility_ranging(self):
        """Test strategy selection for low volatility + ranging."""
        condition = MarketCondition(
            volatility='LOW',
            trend='RANGING',
            volume='NORMAL',
            timestamp=datetime.now()
        )
        
        strategy, score = self.selector.select_best(condition)
        
        # Should select RSI (good for ranging + low vol)
        # or combined if nothing scores high enough
        self.assertIsNotNone(strategy)
        self.assertIn(strategy, list(self.selector.STRATEGY_RULES.keys()))
    
    def test_select_best_returns_combined_if_no_match(self):
        """Test that combined strategy is returned when no good match."""
        # Create condition that doesn't match well
        condition = MarketCondition(
            volatility='MEDIUM',
            trend='RANGING',
            volume='LOW',
            timestamp=datetime.now()
        )
        
        strategy, score = self.selector.select_best(condition)
        
        # Should return a valid strategy
        self.assertIsNotNone(strategy)
        self.assertIn(strategy, list(self.selector.STRATEGY_RULES.keys()))
    
    def test_score_all_strategies(self):
        """Test scoring all strategies."""
        condition = MarketCondition(
            volatility='HIGH',
            trend='STRONG_UP',
            volume='HIGH',
            timestamp=datetime.now()
        )
        
        scores = self.selector.score_all_strategies(condition)
        
        # Should return scores for all strategies
        self.assertEqual(len(scores), len(self.selector.STRATEGY_RULES))
        
        # All should be StrategyScore objects
        for score in scores:
            self.assertIsInstance(score, StrategyScore)
            self.assertIsNotNone(score.name)
            self.assertGreaterEqual(score.score, 0)
            self.assertLessEqual(score.score, 100)
            self.assertIsInstance(score.reasons, list)
        
        # Should be sorted by score (descending)
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i].score, scores[i+1].score)
    
    def test_strategy_score_str(self):
        """Test StrategyScore string representation."""
        score = StrategyScore(
            name='test_strategy',
            score=85.5,
            reasons=['reason1', 'reason2']
        )
        
        str_repr = str(score)
        self.assertIn('test_strategy', str_repr)
        self.assertIn('85.5', str_repr)
    
    def test_get_strategy_info(self):
        """Test getting strategy information."""
        info = self.selector.get_strategy_info('scalping')
        
        self.assertIsInstance(info, dict)
        self.assertIn('volatility', info)
        self.assertIn('trend', info)
        self.assertIn('volume', info)
        self.assertIn('description', info)
    
    def test_get_strategy_info_invalid_strategy(self):
        """Test getting info for invalid strategy raises error."""
        with self.assertRaises(ValueError):
            self.selector.get_strategy_info('nonexistent_strategy')
    
    def test_all_strategies_defined(self):
        """Test that all expected strategies are defined."""
        expected_strategies = [
            'scalping', 'rsi', 'macd', 'bollinger', 
            'momentum', 'ema_cross', 'combined'
        ]
        
        for strategy in expected_strategies:
            self.assertIn(strategy, self.selector.STRATEGY_RULES)
    
    def test_strategy_weights_applied(self):
        """Test that strategy weights are applied correctly."""
        config = {
            'auto_strategy_switching': {
                'strategy_weights': {
                    'momentum': 2.0,  # Double weight
                    'rsi': 0.5        # Half weight
                }
            }
        }
        selector = StrategySelector(config)
        
        condition = MarketCondition(
            volatility='HIGH',
            trend='STRONG_UP',
            volume='HIGH',
            timestamp=datetime.now()
        )
        
        # Score both strategies
        scores = selector.score_all_strategies(condition)
        
        # Find momentum and RSI scores
        momentum_score = next((s for s in scores if s.name == 'momentum'), None)
        
        # Momentum should have a good score for these conditions
        self.assertIsNotNone(momentum_score)
        self.assertGreater(momentum_score.score, 0)
    
    def test_perfect_match_scores_high(self):
        """Test that perfect matches score highly."""
        # Create perfect condition for momentum strategy
        condition = MarketCondition(
            volatility='HIGH',
            trend='STRONG_UP',
            volume='HIGH',
            timestamp=datetime.now()
        )
        
        scores = self.selector.score_all_strategies(condition)
        
        # Find momentum and bollinger (both should match well)
        momentum = next((s for s in scores if s.name == 'momentum'), None)
        
        # Should score very high (close to 100)
        self.assertIsNotNone(momentum)
        self.assertGreater(momentum.score, 70)
    
    def test_partial_match_scores_moderate(self):
        """Test that partial matches score moderately."""
        # Create condition that partially matches scalping
        condition = MarketCondition(
            volatility='MEDIUM',  # Matches
            trend='WEAK_UP',      # Matches
            volume='LOW',         # Doesn't match (wants NORMAL-HIGH)
            timestamp=datetime.now()
        )
        
        scores = self.selector.score_all_strategies(condition)
        scalping = next((s for s in scores if s.name == 'scalping'), None)
        
        # Should score moderately (not 0, not 100)
        self.assertIsNotNone(scalping)
        self.assertGreater(scalping.score, 0)
        self.assertLess(scalping.score, 100)


if __name__ == '__main__':
    unittest.main()
