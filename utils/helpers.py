"""
Helper utility functions for the trading bot.
"""

from typing import Union, Optional
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timezone
import time


def round_step_size(value: float, step_size: float) -> float:
    """
    Round a value to the nearest step size.
    
    Args:
        value: Value to round
        step_size: Step size for rounding
        
    Returns:
        Rounded value
    """
    if step_size == 0:
        return value
    
    precision = len(str(step_size).split('.')[-1]) if '.' in str(step_size) else 0
    return round(value - (value % step_size), precision)


def format_quantity(quantity: float, step_size: float) -> float:
    """
    Format quantity according to exchange step size requirements.
    
    Args:
        quantity: Raw quantity
        step_size: Exchange step size
        
    Returns:
        Formatted quantity
    """
    decimal_qty = Decimal(str(quantity))
    decimal_step = Decimal(str(step_size))
    
    # Calculate how many decimal places we need
    if decimal_step == 0:
        return float(quantity)
    
    # Round down to step size
    result = (decimal_qty // decimal_step) * decimal_step
    return float(result)


def calculate_position_size(
    capital: float,
    risk_pct: float,
    entry_price: float,
    stop_loss_price: float,
    leverage: int = 1
) -> float:
    """
    Calculate position size based on risk management rules.
    
    Args:
        capital: Available capital
        risk_pct: Percentage of capital to risk (e.g., 2.0 for 2%)
        entry_price: Entry price
        stop_loss_price: Stop loss price
        leverage: Leverage multiplier
        
    Returns:
        Position size in base currency
    """
    if entry_price <= 0 or stop_loss_price <= 0:
        return 0.0
    
    # Calculate risk amount in USDT
    risk_amount = capital * (risk_pct / 100)
    
    # Calculate price difference percentage
    price_diff_pct = abs((entry_price - stop_loss_price) / entry_price) * 100
    
    if price_diff_pct == 0:
        return 0.0
    
    # Position size = risk amount / price difference percentage
    # With leverage, we can open larger positions
    position_value = (risk_amount / price_diff_pct) * 100 * leverage
    
    # Convert to quantity
    quantity = position_value / entry_price
    
    return quantity


def calculate_pnl(
    entry_price: float,
    exit_price: float,
    quantity: float,
    side: str
) -> float:
    """
    Calculate profit/loss for a trade.
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        quantity: Position quantity
        side: 'long' or 'short'
        
    Returns:
        PnL in USDT
    """
    if side.lower() == 'long':
        return (exit_price - entry_price) * quantity
    else:  # short
        return (entry_price - exit_price) * quantity


def calculate_pnl_percentage(
    entry_price: float,
    exit_price: float,
    side: str
) -> float:
    """
    Calculate profit/loss percentage.
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        side: 'long' or 'short'
        
    Returns:
        PnL percentage
    """
    if entry_price == 0:
        return 0.0
    
    if side.lower() == 'long':
        return ((exit_price - entry_price) / entry_price) * 100
    else:  # short
        return ((entry_price - exit_price) / entry_price) * 100


def get_timestamp_ms() -> int:
    """
    Get current timestamp in milliseconds.
    
    Returns:
        Current timestamp in milliseconds
    """
    return int(time.time() * 1000)


def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    Convert timestamp to datetime object.
    
    Args:
        timestamp: Timestamp in milliseconds
        
    Returns:
        Datetime object in UTC
    """
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convert datetime to timestamp in milliseconds.
    
    Args:
        dt: Datetime object
        
    Returns:
        Timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if denominator is zero
        
    Returns:
        Division result or default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a value as percentage string.
    
    Args:
        value: Value to format
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"


def format_currency(value: float, decimals: int = 2) -> str:
    """
    Format a value as currency string.
    
    Args:
        value: Value to format
        decimals: Number of decimal places
        
    Returns:
        Formatted currency string
    """
    return f"${value:,.{decimals}f}"


def validate_api_credentials(api_key: Optional[str], api_secret: Optional[str]) -> bool:
    """
    Validate that API credentials are provided and not empty.
    
    Args:
        api_key: API key
        api_secret: API secret
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key or not api_secret:
        return False
    
    if api_key.strip() == "" or api_secret.strip() == "":
        return False
    
    if "your_api_key_here" in api_key.lower() or "your_api_secret_here" in api_secret.lower():
        return False
    
    return True


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_value: Minimum value
        max_value: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_value, min(max_value, value))
