"""
Position sizing module.
Supports Kelly Criterion and fixed risk percentage methods.
"""

from typing import Dict, Any, Optional
import math
from loguru import logger


class PositionSizer:
    """Calculates optimal position size based on risk management."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize position sizer.
        
        Args:
            config: Position sizing configuration
        """
        self.config = config
        self.method = config.get('method', 'fixed_risk')
        self.risk_per_trade = config.get('risk_per_trade', 0.02)  # 2%
        self.max_positions = config.get('max_positions', 4)
        
        logger.info(f"Position sizer initialized with method: {self.method}")
    
    def calculate_position_size(self, capital: float, entry_price: float, 
                               stop_loss: float, leverage: int = 1,
                               win_rate: Optional[float] = None,
                               avg_win: Optional[float] = None,
                               avg_loss: Optional[float] = None) -> float:
        """
        Calculate position size based on selected method.
        
        Args:
            capital: Available capital
            entry_price: Entry price
            stop_loss: Stop loss price
            leverage: Leverage multiplier
            win_rate: Historical win rate (for Kelly Criterion)
            avg_win: Average win size (for Kelly Criterion)
            avg_loss: Average loss size (for Kelly Criterion)
            
        Returns:
            Position size in base currency
        """
        if self.method == 'kelly_criterion':
            return self._kelly_criterion(capital, entry_price, stop_loss, leverage,
                                        win_rate, avg_win, avg_loss)
        elif self.method == 'fixed_risk':
            return self._fixed_risk(capital, entry_price, stop_loss, leverage)
        else:
            logger.warning(f"Unknown method: {self.method}, using fixed_risk")
            return self._fixed_risk(capital, entry_price, stop_loss, leverage)
    
    def _fixed_risk(self, capital: float, entry_price: float, 
                   stop_loss: float, leverage: int) -> float:
        """
        Calculate position size using fixed risk percentage.
        
        Args:
            capital: Available capital
            entry_price: Entry price
            stop_loss: Stop loss price
            leverage: Leverage multiplier
            
        Returns:
            Position size
        """
        # Amount willing to risk
        risk_amount = capital * self.risk_per_trade
        
        # Price risk per unit
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            logger.warning("Price risk is zero, cannot calculate position size")
            return 0
        
        # Position size without leverage
        base_size = risk_amount / price_risk
        
        # Apply leverage (allows larger position but same dollar risk)
        position_size = base_size * leverage
        
        # Cap at maximum capital allocation
        max_size = (capital * leverage) / entry_price
        position_size = min(position_size, max_size)
        
        logger.debug(f"Fixed risk position size: {position_size} (risk={self.risk_per_trade*100}%)")
        return position_size
    
    def _kelly_criterion(self, capital: float, entry_price: float, 
                        stop_loss: float, leverage: int,
                        win_rate: Optional[float], avg_win: Optional[float],
                        avg_loss: Optional[float]) -> float:
        """
        Calculate position size using Kelly Criterion.
        
        Kelly % = W - [(1 - W) / R]
        Where:
        W = Win rate
        R = Ratio of average win to average loss
        
        Args:
            capital: Available capital
            entry_price: Entry price
            stop_loss: Stop loss price
            leverage: Leverage multiplier
            win_rate: Historical win rate (0-1)
            avg_win: Average win size (as percentage)
            avg_loss: Average loss size (as percentage)
            
        Returns:
            Position size
        """
        # Check if we have sufficient statistics
        if win_rate is None or avg_win is None or avg_loss is None:
            logger.warning("Insufficient statistics for Kelly Criterion, using fixed risk")
            return self._fixed_risk(capital, entry_price, stop_loss, leverage)
        
        # Validate inputs
        if win_rate <= 0 or win_rate >= 1:
            logger.warning(f"Invalid win rate: {win_rate}, using fixed risk")
            return self._fixed_risk(capital, entry_price, stop_loss, leverage)
        
        if avg_loss == 0:
            logger.warning("Average loss is zero, using fixed risk")
            return self._fixed_risk(capital, entry_price, stop_loss, leverage)
        
        # Calculate win/loss ratio
        win_loss_ratio = abs(avg_win / avg_loss)
        
        # Calculate Kelly percentage
        kelly_percent = win_rate - ((1 - win_rate) / win_loss_ratio)
        
        # Cap Kelly percentage (use fractional Kelly for safety)
        # Full Kelly can be aggressive, so use 25-50% of Kelly
        kelly_fraction = self.config.get('kelly_fraction', 0.25)
        kelly_percent = max(0, min(kelly_percent * kelly_fraction, 0.1))  # Cap at 10%
        
        if kelly_percent <= 0:
            logger.warning("Kelly percentage <= 0, using minimum risk")
            kelly_percent = 0.01  # Use 1% minimum
        
        # Calculate position size
        risk_amount = capital * kelly_percent
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            logger.warning("Price risk is zero, cannot calculate position size")
            return 0
        
        base_size = risk_amount / price_risk
        position_size = base_size * leverage
        
        # Cap at maximum capital allocation
        max_size = (capital * leverage) / entry_price
        position_size = min(position_size, max_size)
        
        logger.debug(f"Kelly position size: {position_size} (Kelly%={kelly_percent*100:.2f}%)")
        return position_size
    
    def adjust_for_open_positions(self, position_size: float, 
                                  current_positions: int) -> float:
        """
        Adjust position size based on number of open positions.
        
        Args:
            position_size: Calculated position size
            current_positions: Number of currently open positions
            
        Returns:
            Adjusted position size
        """
        if current_positions >= self.max_positions:
            logger.warning(f"Maximum positions reached ({self.max_positions})")
            return 0
        
        # Reduce size if approaching max positions
        if current_positions > self.max_positions / 2:
            reduction_factor = 1 - (current_positions / (self.max_positions * 2))
            adjusted_size = position_size * reduction_factor
            logger.debug(f"Position size reduced due to open positions: {adjusted_size}")
            return adjusted_size
        
        return position_size
    
    def validate_position_size(self, position_size: float, entry_price: float,
                              capital: float, leverage: int,
                              min_order_size: float = 0.001,
                              max_order_size: Optional[float] = None) -> float:
        """
        Validate and adjust position size to meet exchange requirements.
        
        Args:
            position_size: Calculated position size
            entry_price: Entry price
            capital: Available capital
            leverage: Leverage multiplier
            min_order_size: Minimum order size (exchange limit)
            max_order_size: Maximum order size (optional)
            
        Returns:
            Validated position size
        """
        # Check minimum size
        if position_size < min_order_size:
            logger.warning(f"Position size {position_size} below minimum {min_order_size}")
            return 0
        
        # Check maximum size if specified
        if max_order_size and position_size > max_order_size:
            logger.warning(f"Position size {position_size} exceeds maximum {max_order_size}")
            position_size = max_order_size
        
        # Check capital constraint
        required_capital = (position_size * entry_price) / leverage
        if required_capital > capital:
            logger.warning(f"Insufficient capital: required {required_capital}, available {capital}")
            position_size = (capital * leverage) / entry_price
        
        return position_size
    
    def calculate_risk_amount(self, position_size: float, entry_price: float,
                            stop_loss: float) -> float:
        """
        Calculate the dollar risk for a position.
        
        Args:
            position_size: Position size
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Risk amount in dollars
        """
        price_risk = abs(entry_price - stop_loss)
        risk_amount = position_size * price_risk
        
        return risk_amount
    
    def get_max_position_value(self, capital: float, leverage: int,
                              allocation: float = 1.0) -> float:
        """
        Calculate maximum position value.
        
        Args:
            capital: Available capital
            leverage: Leverage multiplier
            allocation: Allocation percentage (0-1)
            
        Returns:
            Maximum position value
        """
        max_value = capital * leverage * allocation
        
        return max_value
