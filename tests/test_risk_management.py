"""
Unit tests for risk management modules.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.risk_management import StopLossManager, TakeProfitManager, PositionSizer


@pytest.fixture
def sample_market_data():
    """Create sample market data."""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1min')
    
    np.random.seed(42)
    close = 50000 + np.cumsum(np.random.randn(100) * 100)
    
    df = pd.DataFrame({
        'high': close + np.abs(np.random.randn(100) * 50),
        'low': close - np.abs(np.random.randn(100) * 50),
        'close': close,
    }, index=dates)
    
    return df


class TestStopLossManager:
    """Tests for StopLossManager."""
    
    def test_percentage_stop_loss(self):
        """Test percentage-based stop loss."""
        config = {'type': 'percentage', 'value': 0.02}
        manager = StopLossManager(config)
        
        # Long position
        stop = manager.calculate_stop_loss(50000, 'long')
        assert stop == 50000 * 0.98
        
        # Short position
        stop = manager.calculate_stop_loss(50000, 'short')
        assert stop == 50000 * 1.02
    
    def test_atr_stop_loss(self, sample_market_data):
        """Test ATR-based stop loss."""
        config = {'type': 'atr', 'multiplier': 2.0, 'atr_period': 14}
        manager = StopLossManager(config)
        
        stop = manager.calculate_stop_loss(50000, 'long', sample_market_data)
        assert isinstance(stop, float)
        assert stop < 50000  # Long stop should be below entry
    
    def test_trailing_stop(self):
        """Test trailing stop loss."""
        config = {
            'type': 'trailing',
            'initial_stop': 0.015,
            'trailing_percent': 0.01,
            'activation_percent': 0.01
        }
        manager = StopLossManager(config)
        
        entry_price = 50000
        stop = manager.set_stop_loss('BTCUSDT', entry_price, 'long')
        
        # Should have initial stop
        assert stop == entry_price * 0.985
        
        # Update with profit
        new_price = 50600  # 1.2% profit
        updated_stop = manager.update_trailing_stop(
            'BTCUSDT', new_price, stop, 'long', entry_price
        )
        
        # Stop should have moved up
        assert updated_stop > stop
    
    def test_stop_hit_detection(self):
        """Test stop hit detection."""
        config = {'type': 'percentage', 'value': 0.02}
        manager = StopLossManager(config)
        
        manager.set_stop_loss('BTCUSDT', 50000, 'long')
        
        # Price above stop - not hit
        assert not manager.check_stop_hit('BTCUSDT', 49500)
        
        # Price below stop - hit
        assert manager.check_stop_hit('BTCUSDT', 48900)


class TestTakeProfitManager:
    """Tests for TakeProfitManager."""
    
    def test_risk_reward_take_profit(self):
        """Test risk/reward ratio take profit."""
        config = {'type': 'risk_reward', 'ratio': 2.0}
        manager = TakeProfitManager(config)
        
        entry_price = 50000
        stop_loss = 49000
        
        targets = manager.calculate_take_profit(entry_price, stop_loss, 'long')
        
        assert len(targets) > 0
        tp_price, size = targets[0]
        
        # TP should be 2x the risk distance
        risk = entry_price - stop_loss
        expected_tp = entry_price + (risk * 2)
        
        assert abs(tp_price - expected_tp) < 0.01
    
    def test_multi_level_take_profit(self):
        """Test multi-level take profit."""
        config = {
            'type': 'multi_level',
            'levels': [
                {'percentage': 0.02, 'exit_size': 0.33},
                {'percentage': 0.04, 'exit_size': 0.33},
                {'percentage': 0.06, 'exit_size': 0.34}
            ]
        }
        manager = TakeProfitManager(config)
        
        targets = manager.calculate_take_profit(50000, 49000, 'long')
        
        assert len(targets) == 3
        
        # Check percentages
        tp1 = targets[0][0]
        assert abs(tp1 - 50000 * 1.02) < 0.01
    
    def test_take_profit_hit_detection(self):
        """Test take profit hit detection."""
        config = {'type': 'risk_reward', 'ratio': 2.0}
        manager = TakeProfitManager(config)
        
        manager.set_take_profit('BTCUSDT', 50000, 49000, 'long')
        
        # Price below TP - not hit
        result = manager.check_take_profit_hit('BTCUSDT', 50500)
        assert result is None
        
        # Price above TP - hit
        result = manager.check_take_profit_hit('BTCUSDT', 52100)
        assert result is not None


class TestPositionSizer:
    """Tests for PositionSizer."""
    
    def test_fixed_risk_sizing(self):
        """Test fixed risk position sizing."""
        config = {'method': 'fixed_risk', 'risk_per_trade': 0.02}
        sizer = PositionSizer(config)
        
        capital = 10000
        entry_price = 50000
        stop_loss = 49000
        leverage = 10
        
        size = sizer.calculate_position_size(capital, entry_price, stop_loss, leverage)
        
        # Should risk 2% of capital
        risk_amount = capital * 0.02
        expected_size = (risk_amount / (entry_price - stop_loss)) * leverage
        
        assert abs(size - expected_size) < 0.0001
    
    def test_kelly_criterion_sizing(self):
        """Test Kelly Criterion position sizing."""
        config = {'method': 'kelly_criterion', 'kelly_fraction': 0.25}
        sizer = PositionSizer(config)
        
        size = sizer.calculate_position_size(
            capital=10000,
            entry_price=50000,
            stop_loss=49000,
            leverage=10,
            win_rate=0.6,
            avg_win=0.02,
            avg_loss=0.01
        )
        
        assert size > 0
        assert isinstance(size, float)
    
    def test_position_size_validation(self):
        """Test position size validation."""
        config = {'method': 'fixed_risk', 'risk_per_trade': 0.02}
        sizer = PositionSizer(config)
        
        # Valid size
        size = sizer.validate_position_size(
            position_size=0.5,
            entry_price=50000,
            capital=10000,
            leverage=10,
            min_order_size=0.001
        )
        assert size == 0.5
        
        # Below minimum
        size = sizer.validate_position_size(
            position_size=0.0001,
            entry_price=50000,
            capital=10000,
            leverage=10,
            min_order_size=0.001
        )
        assert size == 0
    
    def test_risk_calculation(self):
        """Test risk amount calculation."""
        config = {'method': 'fixed_risk', 'risk_per_trade': 0.02}
        sizer = PositionSizer(config)
        
        risk = sizer.calculate_risk_amount(
            position_size=0.1,
            entry_price=50000,
            stop_loss=49000
        )
        
        expected_risk = 0.1 * (50000 - 49000)
        assert abs(risk - expected_risk) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
