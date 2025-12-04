"""
Mock Trading Bot

A simple mock implementation for testing the auto-strategy switching system.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class MockBot:
    """
    Mock trading bot for testing auto-strategy switching.
    
    Simulates a simple trading bot with market data generation.
    """
    
    def __init__(self, initial_strategy: str = 'combined'):
        """
        Initialize mock bot.
        
        Args:
            initial_strategy: Initial trading strategy
        """
        self.current_strategy = initial_strategy
        self.has_positions = False
        logger.info(f"MockBot initialized with strategy: {initial_strategy}")
    
    def get_current_strategy(self) -> str:
        """Get current trading strategy."""
        return self.current_strategy
    
    def set_strategy(self, strategy_name: str) -> bool:
        """
        Set new trading strategy.
        
        Args:
            strategy_name: Name of strategy to use
            
        Returns:
            True if successful
        """
        logger.info(f"Setting strategy: {self.current_strategy} → {strategy_name}")
        self.current_strategy = strategy_name
        return True
    
    def has_open_positions(self) -> bool:
        """Check if there are open positions."""
        return self.has_positions
    
    def close_all_positions(self) -> bool:
        """
        Close all open positions.
        
        Returns:
            True if successful
        """
        if self.has_positions:
            logger.info("Closing all positions")
            self.has_positions = False
            return True
        return True
    
    def get_market_data(self, periods: int = 100) -> pd.DataFrame:
        """
        Generate mock market data.
        
        Args:
            periods: Number of candles to generate
            
        Returns:
            DataFrame with OHLCV data
        """
        # Generate realistic-looking price data
        np.random.seed(int(datetime.now().timestamp()) % 10000)
        
        # Start price
        base_price = 50000
        
        # Generate random walk with trend
        trend = np.random.choice([-1, 0, 1], p=[0.3, 0.4, 0.3])  # Down, sideways, up
        volatility = np.random.choice([0.001, 0.002, 0.004], p=[0.3, 0.4, 0.3])  # Low, medium, high
        
        # Price series
        returns = np.random.normal(trend * 0.0005, volatility, periods)
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Generate OHLC from close prices
        data = []
        for i, close in enumerate(prices):
            # Add some randomness to OHLC
            noise = np.random.uniform(0.9995, 1.0005)
            high = close * noise * (1 + abs(np.random.normal(0, volatility)))
            low = close * noise * (1 - abs(np.random.normal(0, volatility)))
            open_price = close * np.random.uniform(0.999, 1.001)
            
            # Volume with some correlation to volatility
            base_volume = 1000
            volume = base_volume * np.random.uniform(0.5, 2.0) * (1 + volatility * 100)
            
            data.append({
                'open': open_price,
                'high': max(high, close, open_price),
                'low': min(low, close, open_price),
                'close': close,
                'volume': volume
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Add timestamp index
        end_time = datetime.now()
        timestamps = [end_time - timedelta(minutes=5*(periods-i-1)) for i in range(periods)]
        df.index = timestamps
        
        return df
