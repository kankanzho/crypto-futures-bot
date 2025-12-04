"""
Order manager for handling order placement and tracking.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from utils.logger import get_logger

logger = get_logger()


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "Market"
    LIMIT = "Limit"
    STOP_MARKET = "StopMarket"
    STOP_LIMIT = "StopLimit"


@dataclass
class Order:
    """Represents a trading order."""
    symbol: str
    side: str  # 'Buy' or 'Sell'
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    created_time: datetime = field(default_factory=datetime.now)
    filled_time: Optional[datetime] = None
    
    def is_filled(self) -> bool:
        """Check if order is filled."""
        return self.status == OrderStatus.FILLED
    
    def is_active(self) -> bool:
        """Check if order is active (not filled or cancelled)."""
        return self.status in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]
    
    def to_dict(self) -> Dict:
        """Convert order to dictionary."""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'order_type': self.order_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'stop_price': self.stop_price,
            'order_id': self.order_id,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'avg_fill_price': self.avg_fill_price,
            'created_time': self.created_time.isoformat(),
            'filled_time': self.filled_time.isoformat() if self.filled_time else None
        }


class OrderManager:
    """Manages order placement and tracking."""
    
    def __init__(self, api_client):
        """
        Initialize order manager.
        
        Args:
            api_client: Bybit API client instance
        """
        self.api = api_client
        self.active_orders: Dict[str, Order] = {}  # order_id -> Order
        self.order_history: List[Order] = []
        
        logger.info("Order Manager initialized")
    
    def create_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        reduce_only: bool = False
    ) -> Optional[Order]:
        """
        Create a market order.
        
        Args:
            symbol: Trading symbol
            side: 'Buy' or 'Sell'
            quantity: Order quantity
            reduce_only: Whether this is a reduce-only order
            
        Returns:
            Created Order object or None if failed
        """
        # Create order object
        order = Order(
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity
        )
        
        # Place order via API
        result = self.api.place_order(
            symbol=symbol,
            side=side,
            order_type='Market',
            qty=quantity,
            reduce_only=reduce_only
        )
        
        if result and 'orderId' in result:
            order.order_id = result['orderId']
            order.status = OrderStatus.FILLED  # Market orders fill immediately
            order.filled_time = datetime.now()
            
            self.order_history.append(order)
            
            logger.info(f"Market order placed: {symbol} {side} {quantity}")
            return order
        else:
            order.status = OrderStatus.REJECTED
            logger.error(f"Failed to place market order: {symbol} {side} {quantity}")
            return None
    
    def create_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC"
    ) -> Optional[Order]:
        """
        Create a limit order.
        
        Args:
            symbol: Trading symbol
            side: 'Buy' or 'Sell'
            quantity: Order quantity
            price: Limit price
            time_in_force: Time in force (GTC, IOC, FOK)
            
        Returns:
            Created Order object or None if failed
        """
        # Create order object
        order = Order(
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price
        )
        
        # Place order via API
        result = self.api.place_order(
            symbol=symbol,
            side=side,
            order_type='Limit',
            qty=quantity,
            price=price,
            time_in_force=time_in_force
        )
        
        if result and 'orderId' in result:
            order.order_id = result['orderId']
            self.active_orders[order.order_id] = order
            
            logger.info(f"Limit order placed: {symbol} {side} {quantity} @ {price}")
            return order
        else:
            order.status = OrderStatus.REJECTED
            logger.error(f"Failed to place limit order: {symbol} {side} {quantity} @ {price}")
            return None
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel an active order.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID to cancel
            
        Returns:
            True if successful
        """
        if order_id not in self.active_orders:
            logger.warning(f"Order not found: {order_id}")
            return False
        
        # Cancel via API
        success = self.api.cancel_order(symbol=symbol, order_id=order_id)
        
        if success:
            order = self.active_orders.pop(order_id)
            order.status = OrderStatus.CANCELLED
            self.order_history.append(order)
            
            logger.info(f"Order cancelled: {order_id}")
            return True
        else:
            logger.error(f"Failed to cancel order: {order_id}")
            return False
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """
        Cancel all active orders for a symbol or all symbols.
        
        Args:
            symbol: Trading symbol (optional, if None cancels all)
            
        Returns:
            Number of orders cancelled
        """
        cancelled_count = 0
        
        orders_to_cancel = list(self.active_orders.values())
        if symbol:
            orders_to_cancel = [o for o in orders_to_cancel if o.symbol == symbol]
        
        for order in orders_to_cancel:
            if self.cancel_order(order.symbol, order.order_id):
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} orders")
        return cancelled_count
    
    def update_order_status(self, order_id: str, status: OrderStatus) -> None:
        """
        Update order status.
        
        Args:
            order_id: Order ID
            status: New status
        """
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
            order.status = status
            
            if status == OrderStatus.FILLED:
                order.filled_time = datetime.now()
                self.active_orders.pop(order_id)
                self.order_history.append(order)
                logger.info(f"Order filled: {order_id}")
    
    def get_active_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        Get active orders.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of active Order objects
        """
        orders = list(self.active_orders.values())
        
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        
        return orders
    
    def get_order_history(self, symbol: Optional[str] = None, limit: int = 20) -> List[Order]:
        """
        Get order history.
        
        Args:
            symbol: Filter by symbol (optional)
            limit: Maximum number of orders to return
            
        Returns:
            List of historical Order objects
        """
        history = self.order_history
        
        if symbol:
            history = [o for o in history if o.symbol == symbol]
        
        return history[-limit:]
    
    def sync_orders(self) -> None:
        """
        Sync orders with exchange.
        Updates status of active orders.
        """
        try:
            # Get open orders from exchange
            open_orders = self.api.get_open_orders()
            
            # Create a set of exchange order IDs
            exchange_order_ids = {order['orderId'] for order in open_orders}
            
            # Check active orders
            for order_id, order in list(self.active_orders.items()):
                if order_id not in exchange_order_ids:
                    # Order not found on exchange, assume filled or cancelled
                    logger.info(f"Order {order_id} not found on exchange, marking as filled")
                    self.update_order_status(order_id, OrderStatus.FILLED)
            
            # Add any orders from exchange not in our tracking
            for exchange_order in open_orders:
                order_id = exchange_order['orderId']
                if order_id not in self.active_orders:
                    logger.warning(f"Found untracked order on exchange: {order_id}")
                    # Could create Order object from exchange data here
                    
        except Exception as e:
            logger.error(f"Error syncing orders: {e}")
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get a specific order.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order object or None if not found
        """
        # Check active orders first
        if order_id in self.active_orders:
            return self.active_orders[order_id]
        
        # Check history
        for order in self.order_history:
            if order.order_id == order_id:
                return order
        
        return None
    
    def clear_history(self) -> None:
        """Clear order history."""
        self.order_history.clear()
        logger.info("Order history cleared")
