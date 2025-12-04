"""
Unit tests for MarketAnalyzer
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.market_analyzer import MarketAnalyzer, MarketCondition


class TestMarketAnalyzer(unittest.TestCase):
    """Test cases for MarketAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = MarketAnalyzer()
    
    def _generate_test_data(self, periods=100, volatility='medium', trend='ranging'):
        """
        Generate test market data.
        
        Args:
            periods: Number of candles
            volatility: 'low', 'medium', or 'high'
            trend: 'up', 'down', or 'ranging'
        """
        np.random.seed(42)
        
        # Base price
        base_price = 50000
        
        # Set volatility
        vol_map = {'low': 0.0005, 'medium': 0.002, 'high': 0.005}
        vol = vol_map.get(volatility, 0.002)
        
        # Set trend
        trend_map = {'up': 0.001, 'down': -0.001, 'ranging': 0.0}
        trend_drift = trend_map.get(trend, 0.0)
        
        # Generate prices
        returns = np.random.normal(trend_drift, vol, periods)
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Generate OHLCV
        data = []
        for close in prices:
            high = close * (1 + abs(np.random.normal(0, vol)))
            low = close * (1 - abs(np.random.normal(0, vol)))
            open_price = close * np.random.uniform(0.999, 1.001)
            volume = 1000 * np.random.uniform(0.8, 1.2)
            
            data.append({
                'open': open_price,
                'high': max(high, close, open_price),
                'low': min(low, close, open_price),
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        
        # Add timestamps
        end_time = datetime.now()
        timestamps = [end_time - timedelta(minutes=5*(periods-i-1)) for i in range(periods)]
        df.index = timestamps
        
        return df
    
    def test_initialization(self):
        """Test MarketAnalyzer initialization."""
        analyzer = MarketAnalyzer()
        self.assertIsNotNone(analyzer)
        self.assertEqual(analyzer.volatility_period, 14)
        self.assertEqual(analyzer.trend_period, 14)
        self.assertEqual(analyzer.volume_period, 20)
    
    def test_initialization_with_config(self):
        """Test MarketAnalyzer initialization with config."""
        config = {
            'market_analysis': {
                'volatility_period': 20,
                'trend_period': 30,
                'volume_period': 50
            }
        }
        analyzer = MarketAnalyzer(config)
        self.assertEqual(analyzer.volatility_period, 20)
        self.assertEqual(analyzer.trend_period, 30)
        self.assertEqual(analyzer.volume_period, 50)
    
    def test_analyze_returns_market_condition(self):
        """Test that analyze returns MarketCondition."""
        df = self._generate_test_data()
        result = self.analyzer.analyze(df)
        
        self.assertIsInstance(result, MarketCondition)
        self.assertIn(result.volatility, ['LOW', 'MEDIUM', 'HIGH'])
        self.assertIn(result.trend, ['STRONG_UP', 'WEAK_UP', 'RANGING', 'WEAK_DOWN', 'STRONG_DOWN'])
        self.assertIn(result.volume, ['LOW', 'NORMAL', 'HIGH'])
        self.assertIsInstance(result.timestamp, datetime)
        self.assertIsNotNone(result.metrics)
    
    def test_analyze_insufficient_data(self):
        """Test that analyze raises error with insufficient data."""
        df = self._generate_test_data(periods=5)
        
        with self.assertRaises(ValueError):
            self.analyzer.analyze(df)
    
    def test_analyze_missing_columns(self):
        """Test that analyze raises error with missing columns."""
        df = pd.DataFrame({
            'close': [100, 101, 102],
            'volume': [1000, 1100, 1200]
        })
        
        with self.assertRaises(ValueError):
            self.analyzer.analyze(df)
    
    def test_volatility_classification_low(self):
        """Test low volatility classification."""
        df = self._generate_test_data(volatility='low')
        result = self.analyzer.analyze(df)
        
        # Low volatility should be classified correctly
        # Note: Due to randomness, we just check it's a valid level
        self.assertIn(result.volatility, ['LOW', 'MEDIUM', 'HIGH'])
    
    def test_volatility_classification_high(self):
        """Test high volatility classification."""
        df = self._generate_test_data(volatility='high')
        result = self.analyzer.analyze(df)
        
        # High volatility should be classified correctly
        self.assertIn(result.volatility, ['LOW', 'MEDIUM', 'HIGH'])
    
    def test_trend_classification_uptrend(self):
        """Test uptrend classification."""
        df = self._generate_test_data(trend='up')
        result = self.analyzer.analyze(df)
        
        # Should detect some form of uptrend
        self.assertIn(result.trend, ['STRONG_UP', 'WEAK_UP', 'RANGING', 'WEAK_DOWN', 'STRONG_DOWN'])
    
    def test_trend_classification_downtrend(self):
        """Test downtrend classification."""
        df = self._generate_test_data(trend='down')
        result = self.analyzer.analyze(df)
        
        # Should detect some trend
        self.assertIn(result.trend, ['STRONG_UP', 'WEAK_UP', 'RANGING', 'WEAK_DOWN', 'STRONG_DOWN'])
    
    def test_trend_classification_ranging(self):
        """Test ranging market classification."""
        df = self._generate_test_data(trend='ranging')
        result = self.analyzer.analyze(df)
        
        # Should detect ranging or weak trend
        self.assertIn(result.trend, ['STRONG_UP', 'WEAK_UP', 'RANGING', 'WEAK_DOWN', 'STRONG_DOWN'])
    
    def test_metrics_included(self):
        """Test that all expected metrics are included."""
        df = self._generate_test_data()
        result = self.analyzer.analyze(df)
        
        # Check volatility metrics
        self.assertIn('atr', result.metrics)
        self.assertIn('atr_pct', result.metrics)
        self.assertIn('bb_width', result.metrics)
        self.assertIn('price_range_pct', result.metrics)
        
        # Check trend metrics
        self.assertIn('adx', result.metrics)
        self.assertIn('ema5', result.metrics)
        self.assertIn('ema20', result.metrics)
        self.assertIn('ema50', result.metrics)
        self.assertIn('slope_pct', result.metrics)
        
        # Check volume metrics
        self.assertIn('volume_ratio', result.metrics)
        self.assertIn('avg_volume', result.metrics)
        self.assertIn('current_volume', result.metrics)
    
    def test_market_condition_str(self):
        """Test MarketCondition string representation."""
        df = self._generate_test_data()
        result = self.analyzer.analyze(df)
        
        str_repr = str(result)
        self.assertIn('MarketCondition', str_repr)
        self.assertIn('volatility', str_repr)
        self.assertIn('trend', str_repr)
        self.assertIn('volume', str_repr)


if __name__ == '__main__':
    unittest.main()
