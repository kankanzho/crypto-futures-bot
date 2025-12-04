"""
Unit tests for RSI strategy.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategies import RSIStrategy, SignalType


@pytest.fixture
def sample_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1min')
    
    # Create trending data
    np.random.seed(42)
    close_prices = 50000 + np.cumsum(np.random.randn(100) * 100)
    
    df = pd.DataFrame({
        'open': close_prices + np.random.randn(100) * 10,
        'high': close_prices + np.abs(np.random.randn(100) * 20),
        'low': close_prices - np.abs(np.random.randn(100) * 20),
        'close': close_prices,
        'volume': np.random.randint(100, 1000, 100)
    }, index=dates)
    
    return df


@pytest.fixture
def rsi_strategy():
    """Create RSI strategy instance."""
    parameters = {
        'period': 14,
        'oversold': 30,
        'overbought': 70
    }
    return RSIStrategy(parameters)


def test_strategy_initialization(rsi_strategy):
    """Test strategy initialization."""
    assert rsi_strategy.name == "RSI Strategy"
    assert rsi_strategy.period == 14
    assert rsi_strategy.oversold == 30
    assert rsi_strategy.overbought == 70
    assert rsi_strategy.enabled == True


def test_calculate_indicators(rsi_strategy, sample_data):
    """Test indicator calculation."""
    df = rsi_strategy.calculate_indicators(sample_data)
    
    assert 'rsi' in df.columns
    assert len(df) == len(sample_data)
    
    # RSI should be between 0 and 100
    rsi_values = df['rsi'].dropna()
    assert all(rsi_values >= 0)
    assert all(rsi_values <= 100)


def test_generate_signal(rsi_strategy, sample_data):
    """Test signal generation."""
    signal = rsi_strategy.generate_signal('BTCUSDT', sample_data)
    
    assert isinstance(signal, SignalType)
    assert signal in [SignalType.BUY, SignalType.SELL, SignalType.HOLD,
                     SignalType.CLOSE_LONG, SignalType.CLOSE_SHORT]


def test_position_management(rsi_strategy):
    """Test position tracking."""
    assert not rsi_strategy.has_position('BTCUSDT')
    
    # Update position
    rsi_strategy.update_position('BTCUSDT', 'long', 0.1, 50000)
    
    assert rsi_strategy.has_position('BTCUSDT')
    position = rsi_strategy.get_position('BTCUSDT')
    assert position['side'] == 'long'
    assert position['size'] == 0.1
    assert position['entry_price'] == 50000
    
    # Close position
    rsi_strategy.close_position('BTCUSDT')
    assert not rsi_strategy.has_position('BTCUSDT')


def test_parameter_update(rsi_strategy):
    """Test parameter updates."""
    new_params = {'period': 21, 'oversold': 25}
    rsi_strategy.update_parameters(new_params)
    
    assert rsi_strategy.period == 21
    assert rsi_strategy.oversold == 25
    assert rsi_strategy.overbought == 70  # Unchanged


def test_strategy_enable_disable(rsi_strategy):
    """Test enabling/disabling strategy."""
    assert rsi_strategy.enabled == True
    
    rsi_strategy.disable()
    assert rsi_strategy.enabled == False
    
    rsi_strategy.enable()
    assert rsi_strategy.enabled == True


def test_validate_data(rsi_strategy):
    """Test data validation."""
    # Valid data
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1min')
    valid_df = pd.DataFrame({
        'open': range(100),
        'high': range(100),
        'low': range(100),
        'close': range(100),
        'volume': range(100)
    }, index=dates)
    
    assert rsi_strategy.validate_data(valid_df, min_periods=50)
    
    # Insufficient data
    short_df = valid_df.iloc[:10]
    assert not rsi_strategy.validate_data(short_df, min_periods=50)
    
    # Missing columns
    invalid_df = valid_df.drop('volume', axis=1)
    assert not rsi_strategy.validate_data(invalid_df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
