"""
Base strategy class that all trading strategies inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import pandas as pd
from enum import Enum
from loguru import logger


class SignalType(Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""
    
    def __init__(self, name: str, parameters: Dict[str, Any]):
        """
        Initialize base strategy.
        
        Args:
            name: Strategy name
            parameters: Strategy parameters
        """
        self.name = name
        self.parameters = parameters
        self.positions: Dict[str, Dict] = {}  # symbol -> position info
        self.enabled = True
        
        logger.info(f"Strategy initialized: {name}")
    
    @abstractmethod
    def generate_signal(self, symbol: str, data: pd.DataFrame) -> SignalType:
        """
        Generate trading signal based on market data.
        
        Args:
            symbol: Trading pair symbol
            data: OHLCV DataFrame with columns: timestamp, open, high, low, close, volume
            
        Returns:
            SignalType indicating buy, sell, or hold
        """
        pass
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the strategy.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with added indicator columns
        """
        pass
    
    def should_enter_long(self, symbol: str, data: pd.DataFrame) -> bool:
        """
        Check if conditions are met to enter long position.
        
        Args:
            symbol: Trading pair symbol
            data: OHLCV DataFrame with indicators
            
        Returns:
            True if should enter long, False otherwise
        """
        signal = self.generate_signal(symbol, data)
        has_position = self.has_position(symbol)
        
        return signal == SignalType.BUY and not has_position
    
    def should_enter_short(self, symbol: str, data: pd.DataFrame) -> bool:
        """
        Check if conditions are met to enter short position.
        
        Args:
            symbol: Trading pair symbol
            data: OHLCV DataFrame with indicators
            
        Returns:
            True if should enter short, False otherwise
        """
        signal = self.generate_signal(symbol, data)
        has_position = self.has_position(symbol)
        
        return signal == SignalType.SELL and not has_position
    
    def should_exit_long(self, symbol: str, data: pd.DataFrame) -> bool:
        """
        Check if conditions are met to exit long position.
        
        Args:
            symbol: Trading pair symbol
            data: OHLCV DataFrame with indicators
            
        Returns:
            True if should exit long, False otherwise
        """
        signal = self.generate_signal(symbol, data)
        position = self.positions.get(symbol)
        
        if not position or position.get('side') != 'long':
            return False
        
        return signal == SignalType.CLOSE_LONG or signal == SignalType.SELL
    
    def should_exit_short(self, symbol: str, data: pd.DataFrame) -> bool:
        """
        Check if conditions are met to exit short position.
        
        Args:
            symbol: Trading pair symbol
            data: OHLCV DataFrame with indicators
            
        Returns:
            True if should exit short, False otherwise
        """
        signal = self.generate_signal(symbol, data)
        position = self.positions.get(symbol)
        
        if not position or position.get('side') != 'short':
            return False
        
        return signal == SignalType.CLOSE_SHORT or signal == SignalType.BUY
    
    def has_position(self, symbol: str) -> bool:
        """
        Check if there's an open position for symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            True if position exists, False otherwise
        """
        position = self.positions.get(symbol)
        return position is not None and position.get('size', 0) > 0
    
    def update_position(self, symbol: str, side: str, size: float, entry_price: float):
        """
        Update position information.
        
        Args:
            symbol: Trading pair symbol
            side: 'long' or 'short'
            size: Position size
            entry_price: Entry price
        """
        self.positions[symbol] = {
            'side': side,
            'size': size,
            'entry_price': entry_price
        }
        logger.info(f"Position updated: {symbol} {side} {size} @ {entry_price}")
    
    def close_position(self, symbol: str):
        """
        Close position for symbol.
        
        Args:
            symbol: Trading pair symbol
        """
        if symbol in self.positions:
            del self.positions[symbol]
            logger.info(f"Position closed: {symbol}")
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Get position information for symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Position dictionary or None
        """
        return self.positions.get(symbol)
    
    def enable(self):
        """Enable the strategy."""
        self.enabled = True
        logger.info(f"Strategy enabled: {self.name}")
    
    def disable(self):
        """Disable the strategy."""
        self.enabled = False
        logger.info(f"Strategy disabled: {self.name}")
    
    def update_parameters(self, parameters: Dict[str, Any]):
        """
        Update strategy parameters.
        
        Args:
            parameters: New parameters
        """
        self.parameters.update(parameters)
        logger.info(f"Strategy parameters updated: {self.name}")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get strategy information.
        
        Returns:
            Dictionary with strategy info
        """
        return {
            'name': self.name,
            'enabled': self.enabled,
            'parameters': self.parameters,
            'positions': self.positions
        }
    
    def validate_data(self, data: pd.DataFrame, min_periods: int = 100) -> bool:
        """
        Validate that data has enough periods for indicator calculation.
        
        Args:
            data: OHLCV DataFrame
            min_periods: Minimum required periods
            
        Returns:
            True if data is valid, False otherwise
        """
        if data is None or len(data) < min_periods:
            logger.warning(f"Insufficient data: {len(data) if data is not None else 0} < {min_periods}")
            return False
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            logger.warning(f"Missing required columns in data")
            return False
        
        return True
