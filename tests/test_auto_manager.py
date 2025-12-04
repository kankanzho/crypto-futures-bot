"""
Unit tests for AutoStrategyManager
"""

import unittest
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.auto_strategy_manager import AutoStrategyManager
from core.market_analyzer import MarketCondition


class MockBot:
    """Mock bot for testing."""
    
    def __init__(self):
        self.strategy = 'combined'
        self.has_positions = False
        self.set_strategy_calls = []
        self.close_positions_calls = 0
    
    def get_current_strategy(self):
        return self.strategy
    
    def set_strategy(self, name):
        self.set_strategy_calls.append(name)
        self.strategy = name
        return True
    
    def has_open_positions(self):
        return self.has_positions
    
    def close_all_positions(self):
        self.close_positions_calls += 1
        self.has_positions = False
        return True
    
    def get_market_data(self):
        """Generate simple test data."""
        np.random.seed(42)
        periods = 100
        
        data = []
        for i in range(periods):
            close = 50000 + i * 10
            data.append({
                'open': close * 0.999,
                'high': close * 1.001,
                'low': close * 0.998,
                'close': close,
                'volume': 1000
            })
        
        df = pd.DataFrame(data)
        end_time = datetime.now()
        df.index = [end_time - timedelta(minutes=5*(periods-i-1)) for i in range(periods)]
        return df


class TestAutoStrategyManager(unittest.TestCase):
    """Test cases for AutoStrategyManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bot = MockBot()
        self.config = {
            'auto_strategy_switching': {
                'enabled': True,
                'dry_run': True,
                'check_interval': 60,
                'min_strategy_duration': 10,
                'switch_cooldown': 5,
                'score_threshold': 70,
                'close_position_before_switch': False,
                'max_switches_per_hour': 3
            },
            'market_analysis': {
                'volatility_period': 14,
                'trend_period': 14,
                'volume_period': 20
            }
        }
        
        # Use temporary directory for stats file
        self.temp_dir = tempfile.mkdtemp()
        self.test_stats_file = Path(self.temp_dir) / 'test_strategy_switches.json'
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up temporary directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test AutoStrategyManager initialization."""
        manager = AutoStrategyManager(self.bot, self.config)
        
        self.assertIsNotNone(manager)
        self.assertEqual(manager.enabled, True)
        self.assertEqual(manager.dry_run, True)
        self.assertEqual(manager.check_interval, 60)
        self.assertEqual(manager.min_strategy_duration, 10)
        self.assertEqual(manager.current_strategy, 'combined')
    
    def test_initialization_gets_current_strategy(self):
        """Test that initialization gets current strategy from bot."""
        self.bot.strategy = 'momentum'
        manager = AutoStrategyManager(self.bot, self.config)
        
        self.assertEqual(manager.current_strategy, 'momentum')
    
    def test_analyze_and_switch_with_insufficient_data(self):
        """Test analyze_and_switch with insufficient data."""
        manager = AutoStrategyManager(self.bot, self.config)
        
        # Make bot return None
        self.bot.get_market_data = lambda: None
        
        result = manager.analyze_and_switch()
        self.assertFalse(result)
    
    def test_analyze_and_switch_basic(self):
        """Test basic analyze_and_switch functionality."""
        manager = AutoStrategyManager(self.bot, self.config)
        
        # Run analysis
        result = manager.analyze_and_switch()
        
        # Should complete without error
        self.assertIsInstance(result, bool)
    
    def test_should_switch_same_strategy(self):
        """Test that switching to same strategy is rejected."""
        manager = AutoStrategyManager(self.bot, self.config)
        manager.current_strategy = 'momentum'
        
        # Try to switch to same strategy
        result = manager._should_switch('momentum', 80)
        
        self.assertFalse(result)
    
    def test_should_switch_min_duration_not_met(self):
        """Test that minimum duration is enforced."""
        manager = AutoStrategyManager(self.bot, self.config)
        manager.current_strategy = 'scalping'
        manager.strategy_start_time = datetime.now()
        
        # Try to switch immediately (min duration = 10s)
        result = manager._should_switch('momentum', 80)
        
        self.assertFalse(result)
    
    def test_should_switch_low_score(self):
        """Test that low scores are rejected."""
        manager = AutoStrategyManager(self.bot, self.config)
        manager.current_strategy = 'scalping'
        manager.strategy_start_time = datetime.now() - timedelta(seconds=20)
        
        # Try to switch with low score
        result = manager._should_switch('momentum', 50)
        
        self.assertFalse(result)
    
    def test_should_switch_cooldown_active(self):
        """Test that cooldown period is enforced."""
        manager = AutoStrategyManager(self.bot, self.config)
        manager.current_strategy = 'scalping'
        manager.strategy_start_time = datetime.now() - timedelta(seconds=20)
        manager.last_switch_time = datetime.now() - timedelta(seconds=3)
        
        # Try to switch during cooldown (cooldown = 5s)
        result = manager._should_switch('momentum', 80)
        
        self.assertFalse(result)
    
    def test_should_switch_open_positions(self):
        """Test that open positions prevent switching."""
        manager = AutoStrategyManager(self.bot, self.config)
        manager.current_strategy = 'scalping'
        manager.strategy_start_time = datetime.now() - timedelta(seconds=20)
        
        # Set bot to have open positions
        self.bot.has_positions = True
        
        # Try to switch
        result = manager._should_switch('momentum', 80)
        
        self.assertFalse(result)
    
    def test_should_switch_valid_conditions(self):
        """Test that valid conditions allow switching."""
        manager = AutoStrategyManager(self.bot, self.config)
        manager.current_strategy = 'scalping'
        manager.strategy_start_time = datetime.now() - timedelta(seconds=20)
        manager.last_switch_time = datetime.now() - timedelta(seconds=10)
        
        # All conditions met
        result = manager._should_switch('momentum', 80)
        
        self.assertTrue(result)
    
    def test_execute_switch_dry_run(self):
        """Test execute_switch in dry-run mode."""
        manager = AutoStrategyManager(self.bot, self.config)
        manager.dry_run = True
        manager.current_strategy = 'scalping'
        manager.stats_file = self.test_stats_file
        
        condition = MarketCondition(
            volatility='HIGH',
            trend='STRONG_UP',
            volume='HIGH',
            timestamp=datetime.now()
        )
        
        # Execute switch
        result = manager._execute_switch('momentum', condition, 85.0)
        
        self.assertTrue(result)
        self.assertEqual(manager.current_strategy, 'momentum')
        # In dry-run, bot.set_strategy should not be called
        self.assertEqual(len(self.bot.set_strategy_calls), 0)
    
    def test_execute_switch_real_mode(self):
        """Test execute_switch in real mode."""
        manager = AutoStrategyManager(self.bot, self.config)
        manager.dry_run = False
        manager.current_strategy = 'scalping'
        manager.stats_file = self.test_stats_file
        
        condition = MarketCondition(
            volatility='HIGH',
            trend='STRONG_UP',
            volume='HIGH',
            timestamp=datetime.now()
        )
        
        # Execute switch
        result = manager._execute_switch('momentum', condition, 85.0)
        
        self.assertTrue(result)
        self.assertEqual(manager.current_strategy, 'momentum')
        # In real mode, bot.set_strategy should be called
        self.assertEqual(len(self.bot.set_strategy_calls), 1)
        self.assertEqual(self.bot.set_strategy_calls[0], 'momentum')
    
    def test_execute_switch_closes_positions(self):
        """Test that positions are closed if configured."""
        config = self.config.copy()
        config['auto_strategy_switching']['close_position_before_switch'] = True
        
        manager = AutoStrategyManager(self.bot, config)
        manager.dry_run = False
        manager.current_strategy = 'scalping'
        manager.stats_file = self.test_stats_file
        
        # Set bot to have positions
        self.bot.has_positions = True
        
        condition = MarketCondition(
            volatility='HIGH',
            trend='STRONG_UP',
            volume='HIGH',
            timestamp=datetime.now()
        )
        
        # Execute switch
        result = manager._execute_switch('momentum', condition, 85.0)
        
        self.assertTrue(result)
        # Positions should be closed
        self.assertEqual(self.bot.close_positions_calls, 1)
        self.assertFalse(self.bot.has_positions)
    
    def test_is_excessive_switching(self):
        """Test excessive switching detection."""
        manager = AutoStrategyManager(self.bot, self.config)
        manager.stats_file = self.test_stats_file
        
        # Add 3 recent switches
        for i in range(3):
            manager.switch_history.append({
                'timestamp': (datetime.now() - timedelta(minutes=10*i)).isoformat(),
                'from_strategy': 'scalping',
                'to_strategy': 'momentum'
            })
        
        # Should detect excessive switching
        result = manager._is_excessive_switching()
        self.assertTrue(result)
    
    def test_is_not_excessive_switching(self):
        """Test that normal switching is not flagged."""
        manager = AutoStrategyManager(self.bot, self.config)
        manager.stats_file = self.test_stats_file
        
        # Add 2 recent switches
        for i in range(2):
            manager.switch_history.append({
                'timestamp': (datetime.now() - timedelta(minutes=10*i)).isoformat(),
                'from_strategy': 'scalping',
                'to_strategy': 'momentum'
            })
        
        # Should not detect excessive switching
        result = manager._is_excessive_switching()
        self.assertFalse(result)
    
    def test_get_statistics(self):
        """Test getting statistics."""
        manager = AutoStrategyManager(self.bot, self.config)
        manager.current_strategy = 'momentum'
        manager.strategy_start_time = datetime.now() - timedelta(minutes=5)
        
        stats = manager.get_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats['current_strategy'], 'momentum')
        self.assertGreaterEqual(stats['strategy_duration_minutes'], 0)
        self.assertEqual(stats['total_switches'], 0)
    
    def test_save_switch_record(self):
        """Test saving switch records to file."""
        manager = AutoStrategyManager(self.bot, self.config)
        manager.stats_file = self.test_stats_file
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'from_strategy': 'scalping',
            'to_strategy': 'momentum',
            'score': 85.0
        }
        
        manager._save_switch_record(record)
        
        # Check file was created
        self.assertTrue(self.test_stats_file.exists())
        
        # Read and verify
        with open(self.test_stats_file) as f:
            data = json.load(f)
        
        self.assertIn('switches', data)
        self.assertEqual(len(data['switches']), 1)
        self.assertEqual(data['switches'][0]['from_strategy'], 'scalping')


if __name__ == '__main__':
    unittest.main()
