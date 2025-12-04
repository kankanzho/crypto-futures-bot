"""
Risk management system for the trading bot.
Handles position sizing, stop-loss, take-profit, and risk controls.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from utils.logger import get_logger
from utils.helpers import calculate_position_size
from utils.config_loader import get_config

logger = get_logger()


@dataclass
class RiskLimits:
    """Risk limit parameters."""
    max_position_size_pct: float = 25.0  # % of account per position
    max_daily_loss_pct: float = 5.0  # % of account
    risk_per_trade_pct: float = 2.0  # % of account per trade
    max_positions: int = 4
    max_leverage: int = 20


class RiskManager:
    """Manages risk for all trading operations."""
    
    def __init__(self, initial_capital: float):
        """
        Initialize risk manager.
        
        Args:
            initial_capital: Starting capital in USDT
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_limits = RiskLimits()
        
        # Load risk parameters from config
        config = get_config()
        self.risk_limits.max_position_size_pct = config.get('trading.position_size_pct', 25.0)
        self.risk_limits.max_daily_loss_pct = config.get('risk_management.max_daily_loss_pct', 5.0)
        self.risk_limits.risk_per_trade_pct = config.get('risk_management.risk_per_trade_pct', 2.0)
        self.risk_limits.max_positions = config.get('trading.max_positions', 4)
        self.risk_limits.max_leverage = config.get('trading.leverage', 10)
        
        # Risk tracking
        self.daily_pnl = 0.0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.open_positions_count = 0
        self.total_exposure = 0.0
        
        logger.info(f"Risk Manager initialized with capital: ${initial_capital}")
        logger.info(f"Risk limits: {self.risk_limits}")
    
    def update_capital(self, new_capital: float) -> None:
        """
        Update current capital.
        
        Args:
            new_capital: New capital value
        """
        self.current_capital = new_capital
        logger.info(f"Capital updated: ${new_capital:.2f}")
    
    def reset_daily_pnl(self) -> None:
        """Reset daily P&L tracking."""
        now = datetime.now()
        if now >= self.daily_reset_time + timedelta(days=1):
            logger.info(f"Daily P&L reset. Previous: ${self.daily_pnl:.2f}")
            self.daily_pnl = 0.0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def add_trade_pnl(self, pnl: float) -> None:
        """
        Add trade P&L to daily tracking.
        
        Args:
            pnl: Trade P&L in USDT
        """
        self.daily_pnl += pnl
        self.current_capital += pnl
        logger.info(f"Trade P&L: ${pnl:.2f}, Daily P&L: ${self.daily_pnl:.2f}")
    
    def can_open_position(self) -> Tuple[bool, str]:
        """
        Check if a new position can be opened.
        
        Returns:
            Tuple of (allowed, reason)
        """
        # Check daily loss limit
        daily_loss_limit = self.initial_capital * (self.risk_limits.max_daily_loss_pct / 100)
        if self.daily_pnl < -daily_loss_limit:
            return False, f"Daily loss limit reached: ${abs(self.daily_pnl):.2f}"
        
        # Check max positions
        if self.open_positions_count >= self.risk_limits.max_positions:
            return False, f"Max positions limit reached: {self.open_positions_count}"
        
        # Check if enough capital
        if self.current_capital <= 0:
            return False, "Insufficient capital"
        
        return True, "OK"
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: float,
        symbol: str = "BTCUSDT"
    ) -> Dict[str, float]:
        """
        Calculate position size based on risk management rules.
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            symbol: Trading symbol
            
        Returns:
            Dictionary with position sizing information
        """
        # Calculate position size based on risk
        position_qty = calculate_position_size(
            capital=self.current_capital,
            risk_pct=self.risk_limits.risk_per_trade_pct,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            leverage=self.risk_limits.max_leverage
        )
        
        # Calculate position value
        position_value = position_qty * entry_price
        
        # Ensure position doesn't exceed max size
        max_position_value = self.current_capital * (self.risk_limits.max_position_size_pct / 100) * self.risk_limits.max_leverage
        
        if position_value > max_position_value:
            position_qty = max_position_value / entry_price
            position_value = max_position_value
            logger.warning(f"Position size reduced to max limit: {max_position_value:.2f} USDT")
        
        # Calculate risk amount
        risk_amount = abs(entry_price - stop_loss_price) * position_qty
        
        return {
            'quantity': position_qty,
            'value': position_value,
            'risk_amount': risk_amount,
            'risk_pct': (risk_amount / self.current_capital) * 100
        }
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        side: str,
        stop_loss_pct: Optional[float] = None,
        atr: Optional[float] = None,
        use_atr: bool = False,
        atr_multiplier: float = 2.0
    ) -> float:
        """
        Calculate stop loss price.
        
        Args:
            entry_price: Entry price
            side: Position side ('long' or 'short')
            stop_loss_pct: Stop loss percentage (optional)
            atr: Average True Range value (optional)
            use_atr: Whether to use ATR-based stop loss
            atr_multiplier: ATR multiplier for dynamic stop
            
        Returns:
            Stop loss price
        """
        if use_atr and atr:
            # ATR-based stop loss
            if side.lower() == 'long':
                return entry_price - (atr * atr_multiplier)
            else:
                return entry_price + (atr * atr_multiplier)
        else:
            # Percentage-based stop loss
            config = get_config()
            if stop_loss_pct is None:
                stop_loss_pct = config.get('risk_management.stop_loss_pct', 2.0)
            
            if side.lower() == 'long':
                return entry_price * (1 - stop_loss_pct / 100)
            else:
                return entry_price * (1 + stop_loss_pct / 100)
    
    def calculate_take_profit(
        self,
        entry_price: float,
        side: str,
        take_profit_pct: Optional[float] = None,
        risk_reward_ratio: Optional[float] = None,
        stop_loss_price: Optional[float] = None
    ) -> float:
        """
        Calculate take profit price.
        
        Args:
            entry_price: Entry price
            side: Position side ('long' or 'short')
            take_profit_pct: Take profit percentage (optional)
            risk_reward_ratio: Risk-reward ratio (e.g., 2.0 for 1:2)
            stop_loss_price: Stop loss price (required for R:R calculation)
            
        Returns:
            Take profit price
        """
        config = get_config()
        
        if risk_reward_ratio and stop_loss_price:
            # Calculate TP based on risk-reward ratio
            risk_amount = abs(entry_price - stop_loss_price)
            reward_amount = risk_amount * risk_reward_ratio
            
            if side.lower() == 'long':
                return entry_price + reward_amount
            else:
                return entry_price - reward_amount
        else:
            # Percentage-based take profit
            if take_profit_pct is None:
                take_profit_pct = config.get('risk_management.take_profit_pct', 3.0)
            
            if side.lower() == 'long':
                return entry_price * (1 + take_profit_pct / 100)
            else:
                return entry_price * (1 - take_profit_pct / 100)
    
    def update_trailing_stop(
        self,
        entry_price: float,
        current_price: float,
        current_stop: float,
        side: str,
        trailing_pct: Optional[float] = None
    ) -> float:
        """
        Calculate updated trailing stop loss.
        
        Args:
            entry_price: Entry price
            current_price: Current market price
            current_stop: Current stop loss price
            side: Position side ('long' or 'short')
            trailing_pct: Trailing stop percentage (optional)
            
        Returns:
            Updated stop loss price
        """
        config = get_config()
        if trailing_pct is None:
            trailing_pct = config.get('risk_management.trailing_stop_pct', 1.5)
        
        if side.lower() == 'long':
            # Only move stop up for long positions
            new_stop = current_price * (1 - trailing_pct / 100)
            return max(current_stop, new_stop)
        else:
            # Only move stop down for short positions
            new_stop = current_price * (1 + trailing_pct / 100)
            return min(current_stop, new_stop)
    
    def should_partial_take_profit(
        self,
        entry_price: float,
        current_price: float,
        side: str,
        partial_tp_pct: Optional[float] = None
    ) -> bool:
        """
        Check if partial take profit should be executed.
        
        Args:
            entry_price: Entry price
            current_price: Current market price
            side: Position side ('long' or 'short')
            partial_tp_pct: Partial TP trigger percentage
            
        Returns:
            True if partial TP should be executed
        """
        config = get_config()
        if not config.get('risk_management.partial_take_profit', False):
            return False
        
        if partial_tp_pct is None:
            # Use half of full TP as partial trigger
            partial_tp_pct = config.get('risk_management.take_profit_pct', 3.0) / 2
        
        if side.lower() == 'long':
            profit_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            profit_pct = ((entry_price - current_price) / entry_price) * 100
        
        return profit_pct >= partial_tp_pct
    
    def validate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Tuple[bool, str]:
        """
        Validate an order before placement.
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            price: Order price
            
        Returns:
            Tuple of (valid, reason)
        """
        # Check if can open position
        can_open, reason = self.can_open_position()
        if not can_open:
            return False, reason
        
        # Check order value
        order_value = quantity * price
        max_order_value = self.current_capital * (self.risk_limits.max_position_size_pct / 100) * self.risk_limits.max_leverage
        
        if order_value > max_order_value:
            return False, f"Order value exceeds max position size: ${order_value:.2f} > ${max_order_value:.2f}"
        
        # Check if quantity is positive
        if quantity <= 0:
            return False, "Invalid quantity"
        
        return True, "OK"
