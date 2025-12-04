"""
Base strategy class for all trading strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import pandas as pd
from utils.logger import get_logger
from utils.config_loader import get_config

logger = get_logger()


class Signal:
    """Represents a trading signal."""
    
    LONG = 1
    SHORT = -1
    NEUTRAL = 0
    
    def __init__(self, direction: int, strength: float = 1.0, reason: str = ""):
        """
        Initialize signal.
        
        Args:
            direction: Signal direction (1=long, -1=short, 0=neutral)
            strength: Signal strength (0.0 to 1.0)
            reason: Reason for signal
        """
        self.direction = direction
        self.strength = strength
        self.reason = reason
    
    def is_long(self) -> bool:
        """Check if signal is long."""
        return self.direction == self.LONG
    
    def is_short(self) -> bool:
        """Check if signal is short."""
        return self.direction == self.SHORT
    
    def is_neutral(self) -> bool:
        """Check if signal is neutral."""
        return self.direction == self.NEUTRAL
    
    def __repr__(self) -> str:
        direction_str = {1: "LONG", -1: "SHORT", 0: "NEUTRAL"}.get(self.direction, "UNKNOWN")
        return f"Signal({direction_str}, strength={self.strength:.2f}, reason='{self.reason}')"


class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self, name: str, params: Optional[Dict] = None):
        """
        Initialize base strategy.
        
        Args:
            name: Strategy name
            params: Strategy parameters (optional)
        """
        self.name = name
        self.params = params or {}
        
        # Load default params from config if not provided
        if not params:
            config = get_config()
            self.params = config.get_strategy_params(name)
        
        logger.info(f"Strategy '{name}' initialized with params: {self.params}")
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on market data.
        
        Args:
            df: DataFrame with OHLCV data and indicators
            
        Returns:
            Signal object
        """
        pass
    
    def validate_dataframe(self, df: pd.DataFrame, required_columns: list) -> bool:
        """
        Validate that dataframe has required columns.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            True if valid, False otherwise
        """
        if df is None or df.empty:
            logger.warning(f"{self.name}: Empty dataframe")
            return False
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.warning(f"{self.name}: Missing columns: {missing_columns}")
            return False
        
        return True
    
    def get_param(self, key: str, default=None):
        """
        Get strategy parameter.
        
        Args:
            key: Parameter key
            default: Default value if not found
            
        Returns:
            Parameter value
        """
        return self.params.get(key, default)
    
    def check_volume_filter(self, df: pd.DataFrame) -> bool:
        """
        Check if volume is sufficient for trading.
        
        Args:
            df: DataFrame with volume data
            
        Returns:
            True if volume is sufficient
        """
        if 'volume' not in df.columns or 'volume_ma' not in df.columns:
            return True  # Skip filter if data not available
        
        volume_threshold = self.get_param('volume_threshold', 1.5)
        
        latest_volume = df['volume'].iloc[-1]
        avg_volume = df['volume_ma'].iloc[-1]
        
        if pd.isna(avg_volume) or avg_volume == 0:
            return True
        
        return latest_volume >= (avg_volume * volume_threshold)
    
    def check_volatility_filter(self, df: pd.DataFrame) -> bool:
        """
        Check if volatility is sufficient for trading.
        
        Args:
            df: DataFrame with ATR data
            
        Returns:
            True if volatility is sufficient
        """
        if 'atr' not in df.columns:
            return True  # Skip filter if data not available
        
        min_atr = self.get_param('min_atr', 0.0001)
        
        latest_atr = df['atr'].iloc[-1]
        
        if pd.isna(latest_atr):
            return True
        
        return latest_atr >= min_atr
    
    def check_trend_filter(self, df: pd.DataFrame) -> Optional[str]:
        """
        Check current trend direction.
        
        Args:
            df: DataFrame with price and EMA data
            
        Returns:
            'up', 'down', or None if no clear trend
        """
        if 'close' not in df.columns or 'ema_50' not in df.columns:
            return None
        
        latest_close = df['close'].iloc[-1]
        ema_50 = df['ema_50'].iloc[-1]
        
        if pd.isna(ema_50):
            return None
        
        if latest_close > ema_50:
            return 'up'
        elif latest_close < ema_50:
            return 'down'
        else:
            return None
    
    def should_enter_trade(self, signal: Signal, df: pd.DataFrame) -> bool:
        """
        Determine if should enter trade based on signal and filters.
        
        Args:
            signal: Trading signal
            df: DataFrame with market data
            
        Returns:
            True if should enter trade
        """
        if signal.is_neutral():
            return False
        
        # Check volume filter
        config = get_config()
        if config.get('strategies.volume_filter', False):
            if not self.check_volume_filter(df):
                logger.debug(f"{self.name}: Volume filter failed")
                return False
        
        # Check volatility filter
        if config.get('strategies.volatility_filter', False):
            if not self.check_volatility_filter(df):
                logger.debug(f"{self.name}: Volatility filter failed")
                return False
        
        # Check trend filter
        if config.get('strategies.trend_filter', False):
            trend = self.check_trend_filter(df)
            if trend:
                # Only allow longs in uptrend, shorts in downtrend
                if signal.is_long() and trend != 'up':
                    logger.debug(f"{self.name}: Trend filter failed (long in downtrend)")
                    return False
                if signal.is_short() and trend != 'down':
                    logger.debug(f"{self.name}: Trend filter failed (short in uptrend)")
                    return False
        
        return True
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
