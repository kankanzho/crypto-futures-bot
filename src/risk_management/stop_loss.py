"""
Stop loss management module.
Supports percentage-based, ATR-based, and trailing stop losses.
"""

from typing import Dict, Any, Optional
import pandas as pd
from loguru import logger
from ..utils.indicators import calculate_atr


class StopLossManager:
    """Manages stop loss orders for positions."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize stop loss manager.
        
        Args:
            config: Stop loss configuration
        """
        self.config = config
        self.stop_type = config.get('type', 'percentage')
        self.active_stops: Dict[str, Dict] = {}  # symbol -> stop info
        
        logger.info(f"Stop loss manager initialized with type: {self.stop_type}")
    
    def calculate_stop_loss(self, entry_price: float, side: str, 
                           market_data: Optional[pd.DataFrame] = None) -> float:
        """
        Calculate stop loss price.
        
        Args:
            entry_price: Position entry price
            side: 'long' or 'short'
            market_data: Market data for ATR calculation (required for ATR-based stops)
            
        Returns:
            Stop loss price
        """
        if self.stop_type == 'percentage':
            return self._calculate_percentage_stop(entry_price, side)
        elif self.stop_type == 'atr':
            return self._calculate_atr_stop(entry_price, side, market_data)
        elif self.stop_type == 'trailing':
            return self._calculate_trailing_stop(entry_price, side)
        else:
            logger.warning(f"Unknown stop type: {self.stop_type}, using percentage")
            return self._calculate_percentage_stop(entry_price, side)
    
    def _calculate_percentage_stop(self, entry_price: float, side: str) -> float:
        """
        Calculate percentage-based stop loss.
        
        Args:
            entry_price: Position entry price
            side: 'long' or 'short'
            
        Returns:
            Stop loss price
        """
        stop_percent = self.config.get('value', 0.02)  # Default 2%
        
        if side == 'long':
            stop_price = entry_price * (1 - stop_percent)
        else:  # short
            stop_price = entry_price * (1 + stop_percent)
        
        logger.debug(f"Percentage stop: {stop_price} ({stop_percent*100}%)")
        return stop_price
    
    def _calculate_atr_stop(self, entry_price: float, side: str, 
                           market_data: Optional[pd.DataFrame]) -> float:
        """
        Calculate ATR-based stop loss.
        
        Args:
            entry_price: Position entry price
            side: 'long' or 'short'
            market_data: Market data with high, low, close
            
        Returns:
            Stop loss price
        """
        if market_data is None or len(market_data) < 20:
            logger.warning("Insufficient data for ATR, using percentage stop")
            return self._calculate_percentage_stop(entry_price, side)
        
        atr_period = self.config.get('atr_period', 14)
        atr_multiplier = self.config.get('multiplier', 2.0)
        
        # Calculate ATR
        atr = calculate_atr(
            market_data['high'],
            market_data['low'],
            market_data['close'],
            period=atr_period
        )
        
        current_atr = atr.iloc[-1]
        
        if pd.isna(current_atr):
            logger.warning("Invalid ATR value, using percentage stop")
            return self._calculate_percentage_stop(entry_price, side)
        
        # Calculate stop based on ATR
        if side == 'long':
            stop_price = entry_price - (current_atr * atr_multiplier)
        else:  # short
            stop_price = entry_price + (current_atr * atr_multiplier)
        
        logger.debug(f"ATR stop: {stop_price} (ATR={current_atr}, multiplier={atr_multiplier})")
        return stop_price
    
    def _calculate_trailing_stop(self, entry_price: float, side: str) -> float:
        """
        Calculate initial trailing stop loss.
        
        Args:
            entry_price: Position entry price
            side: 'long' or 'short'
            
        Returns:
            Initial stop loss price
        """
        initial_stop_percent = self.config.get('initial_stop', 0.015)  # Default 1.5%
        
        if side == 'long':
            stop_price = entry_price * (1 - initial_stop_percent)
        else:  # short
            stop_price = entry_price * (1 + initial_stop_percent)
        
        logger.debug(f"Initial trailing stop: {stop_price}")
        return stop_price
    
    def update_trailing_stop(self, symbol: str, current_price: float, 
                           current_stop: float, side: str, entry_price: float) -> float:
        """
        Update trailing stop loss based on current price.
        
        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            current_stop: Current stop loss price
            side: 'long' or 'short'
            entry_price: Position entry price
            
        Returns:
            Updated stop loss price
        """
        if self.stop_type != 'trailing':
            return current_stop
        
        trailing_percent = self.config.get('trailing_percent', 0.01)  # Default 1%
        activation_percent = self.config.get('activation_percent', 0.01)  # Default 1% profit
        
        # Calculate if position is in profit enough to activate trailing
        if side == 'long':
            profit_percent = (current_price - entry_price) / entry_price
            is_activated = profit_percent >= activation_percent
            
            if is_activated:
                new_stop = current_price * (1 - trailing_percent)
                # Only move stop up, never down
                return max(current_stop, new_stop)
        else:  # short
            profit_percent = (entry_price - current_price) / entry_price
            is_activated = profit_percent >= activation_percent
            
            if is_activated:
                new_stop = current_price * (1 + trailing_percent)
                # Only move stop down, never up
                return min(current_stop, new_stop)
        
        return current_stop
    
    def set_stop_loss(self, symbol: str, entry_price: float, side: str,
                     market_data: Optional[pd.DataFrame] = None) -> float:
        """
        Set stop loss for a position.
        
        Args:
            symbol: Trading pair symbol
            entry_price: Position entry price
            side: 'long' or 'short'
            market_data: Market data (required for ATR-based stops)
            
        Returns:
            Stop loss price
        """
        stop_price = self.calculate_stop_loss(entry_price, side, market_data)
        
        self.active_stops[symbol] = {
            'price': stop_price,
            'entry_price': entry_price,
            'side': side,
            'type': self.stop_type
        }
        
        logger.info(f"Stop loss set for {symbol}: {stop_price} ({side})")
        return stop_price
    
    def update_stop_loss(self, symbol: str, current_price: float) -> Optional[float]:
        """
        Update stop loss for trailing stops.
        
        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            
        Returns:
            Updated stop loss price or None if no stop exists
        """
        if symbol not in self.active_stops:
            return None
        
        stop_info = self.active_stops[symbol]
        
        if stop_info['type'] == 'trailing':
            new_stop = self.update_trailing_stop(
                symbol,
                current_price,
                stop_info['price'],
                stop_info['side'],
                stop_info['entry_price']
            )
            
            if new_stop != stop_info['price']:
                stop_info['price'] = new_stop
                logger.info(f"Trailing stop updated for {symbol}: {new_stop}")
            
            return new_stop
        
        return stop_info['price']
    
    def check_stop_hit(self, symbol: str, current_price: float) -> bool:
        """
        Check if stop loss has been hit.
        
        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            
        Returns:
            True if stop loss hit, False otherwise
        """
        if symbol not in self.active_stops:
            return False
        
        stop_info = self.active_stops[symbol]
        stop_price = stop_info['price']
        side = stop_info['side']
        
        if side == 'long':
            # Long stop hit when price drops below stop
            return current_price <= stop_price
        else:  # short
            # Short stop hit when price rises above stop
            return current_price >= stop_price
    
    def remove_stop_loss(self, symbol: str):
        """
        Remove stop loss for a symbol.
        
        Args:
            symbol: Trading pair symbol
        """
        if symbol in self.active_stops:
            del self.active_stops[symbol]
            logger.info(f"Stop loss removed for {symbol}")
    
    def get_stop_loss(self, symbol: str) -> Optional[float]:
        """
        Get current stop loss price for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Stop loss price or None
        """
        if symbol in self.active_stops:
            return self.active_stops[symbol]['price']
        return None
