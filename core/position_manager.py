"""
Position manager for tracking and managing open positions.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from utils.logger import get_logger
from utils.helpers import calculate_pnl, calculate_pnl_percentage

logger = get_logger()


@dataclass
class Position:
    """Represents a trading position."""
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    quantity: float
    leverage: int
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_time: datetime = field(default_factory=datetime.now)
    order_id: Optional[str] = None
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    def update_pnl(self, current_price: float) -> None:
        """
        Update unrealized P&L based on current price.
        
        Args:
            current_price: Current market price
        """
        self.unrealized_pnl = calculate_pnl(
            entry_price=self.entry_price,
            exit_price=current_price,
            quantity=self.quantity,
            side=self.side
        )
    
    def get_pnl_percentage(self, current_price: float) -> float:
        """
        Get P&L as percentage.
        
        Args:
            current_price: Current market price
            
        Returns:
            P&L percentage
        """
        return calculate_pnl_percentage(
            entry_price=self.entry_price,
            exit_price=current_price,
            side=self.side
        )
    
    def to_dict(self) -> Dict:
        """Convert position to dictionary."""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'leverage': self.leverage,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'entry_time': self.entry_time.isoformat(),
            'order_id': self.order_id,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl
        }


class PositionManager:
    """Manages all open positions."""
    
    def __init__(self):
        """Initialize position manager."""
        self.positions: Dict[str, Position] = {}  # symbol -> Position
        self.closed_positions: List[Position] = []
        self.total_realized_pnl = 0.0
        
        logger.info("Position Manager initialized")
    
    def add_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        leverage: int,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        order_id: Optional[str] = None
    ) -> Position:
        """
        Add a new position.
        
        Args:
            symbol: Trading symbol
            side: Position side ('long' or 'short')
            entry_price: Entry price
            quantity: Position quantity
            leverage: Leverage used
            stop_loss: Stop loss price
            take_profit: Take profit price
            order_id: Associated order ID
            
        Returns:
            Created Position object
        """
        position = Position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            leverage=leverage,
            stop_loss=stop_loss,
            take_profit=take_profit,
            order_id=order_id
        )
        
        self.positions[symbol] = position
        logger.info(f"Position added: {symbol} {side} {quantity} @ {entry_price}")
        
        return position
    
    def update_position(
        self,
        symbol: str,
        current_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Optional[Position]:
        """
        Update position with current price and optionally update SL/TP.
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            stop_loss: New stop loss price (optional)
            take_profit: New take profit price (optional)
            
        Returns:
            Updated Position or None if not found
        """
        position = self.positions.get(symbol)
        
        if not position:
            return None
        
        # Update P&L
        position.update_pnl(current_price)
        
        # Update stop loss if provided
        if stop_loss is not None:
            position.stop_loss = stop_loss
        
        # Update take profit if provided
        if take_profit is not None:
            position.take_profit = take_profit
        
        return position
    
    def close_position(
        self,
        symbol: str,
        exit_price: float,
        close_reason: str = "manual"
    ) -> Optional[Position]:
        """
        Close a position.
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            close_reason: Reason for closing
            
        Returns:
            Closed Position or None if not found
        """
        position = self.positions.pop(symbol, None)
        
        if not position:
            logger.warning(f"No position found to close: {symbol}")
            return None
        
        # Calculate final P&L
        position.realized_pnl = calculate_pnl(
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            side=position.side
        )
        
        pnl_pct = position.get_pnl_percentage(exit_price)
        
        # Update total realized P&L
        self.total_realized_pnl += position.realized_pnl
        
        # Add to closed positions
        self.closed_positions.append(position)
        
        logger.info(f"Position closed: {symbol} | Reason: {close_reason} | "
                   f"P&L: ${position.realized_pnl:.2f} ({pnl_pct:+.2f}%)")
        
        return position
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get a specific position.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position or None if not found
        """
        return self.positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """
        Check if a position exists.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if position exists
        """
        return symbol in self.positions
    
    def get_all_positions(self) -> List[Position]:
        """
        Get all open positions.
        
        Returns:
            List of Position objects
        """
        return list(self.positions.values())
    
    def get_positions_count(self) -> int:
        """
        Get count of open positions.
        
        Returns:
            Number of open positions
        """
        return len(self.positions)
    
    def get_total_exposure(self) -> float:
        """
        Get total exposure across all positions.
        
        Returns:
            Total exposure in USDT
        """
        total = 0.0
        for position in self.positions.values():
            total += position.entry_price * position.quantity
        return total
    
    def get_unrealized_pnl(self) -> float:
        """
        Get total unrealized P&L across all positions.
        
        Returns:
            Total unrealized P&L in USDT
        """
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        Check if stop loss is hit.
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            True if stop loss is hit
        """
        position = self.positions.get(symbol)
        
        if not position or position.stop_loss is None:
            return False
        
        if position.side.lower() == 'long':
            return current_price <= position.stop_loss
        else:
            return current_price >= position.stop_loss
    
    def check_take_profit(self, symbol: str, current_price: float) -> bool:
        """
        Check if take profit is hit.
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            True if take profit is hit
        """
        position = self.positions.get(symbol)
        
        if not position or position.take_profit is None:
            return False
        
        if position.side.lower() == 'long':
            return current_price >= position.take_profit
        else:
            return current_price <= position.take_profit
    
    def get_position_summary(self) -> Dict:
        """
        Get summary of all positions.
        
        Returns:
            Dictionary with position statistics
        """
        return {
            'open_positions': self.get_positions_count(),
            'total_exposure': self.get_total_exposure(),
            'unrealized_pnl': self.get_unrealized_pnl(),
            'realized_pnl': self.total_realized_pnl,
            'closed_positions_count': len(self.closed_positions)
        }
    
    def get_closed_positions(self, limit: int = 20) -> List[Position]:
        """
        Get recent closed positions.
        
        Args:
            limit: Maximum number of positions to return
            
        Returns:
            List of closed Position objects
        """
        return self.closed_positions[-limit:]
    
    def clear_closed_positions(self) -> None:
        """Clear closed positions history."""
        self.closed_positions.clear()
        logger.info("Closed positions history cleared")
