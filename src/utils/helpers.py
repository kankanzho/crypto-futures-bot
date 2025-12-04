"""
Helper utilities for the crypto futures bot.
"""

import yaml
import os
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def load_strategy_config(config_path: str = "config/strategies.yaml") -> Dict[str, Any]:
    """
    Load strategy configuration from YAML file.
    
    Args:
        config_path: Path to strategy configuration file
        
    Returns:
        Strategy configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def load_env_config():
    """
    Load environment variables from .env file.
    """
    load_dotenv()
    
    return {
        'api_key': os.getenv('BYBIT_API_KEY'),
        'api_secret': os.getenv('BYBIT_API_SECRET'),
        'testnet': os.getenv('BYBIT_TESTNET', 'true').lower() == 'true',
        'initial_capital': float(os.getenv('INITIAL_CAPITAL', 10000)),
        'max_position_size': float(os.getenv('MAX_POSITION_SIZE', 1000))
    }


def format_price(price: float, decimals: int = 2) -> str:
    """
    Format price for display.
    
    Args:
        price: Price value
        decimals: Number of decimal places
        
    Returns:
        Formatted price string
    """
    return f"${price:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format percentage for display.
    
    Args:
        value: Percentage value (as decimal, e.g., 0.05 for 5%)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def calculate_position_size(capital: float, risk_percent: float, entry_price: float, 
                           stop_loss_price: float, leverage: int = 1) -> float:
    """
    Calculate position size based on risk management.
    
    Args:
        capital: Available capital
        risk_percent: Risk percentage per trade (e.g., 0.02 for 2%)
        entry_price: Entry price
        stop_loss_price: Stop loss price
        leverage: Leverage multiplier
        
    Returns:
        Position size in base currency
    """
    risk_amount = capital * risk_percent
    price_risk = abs(entry_price - stop_loss_price)
    
    if price_risk == 0:
        return 0
    
    position_size = (risk_amount / price_risk) * leverage
    
    return position_size


def validate_api_credentials(api_key: str, api_secret: str) -> bool:
    """
    Validate that API credentials are set.
    
    Args:
        api_key: API key
        api_secret: API secret
        
    Returns:
        True if credentials are valid, False otherwise
    """
    if not api_key or api_key == "your_api_key_here":
        return False
    if not api_secret or api_secret == "your_api_secret_here":
        return False
    return True


def ensure_directories():
    """
    Ensure all required directories exist.
    """
    directories = ['data', 'logs', 'results', 'config']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)


def round_to_tick(price: float, tick_size: float) -> float:
    """
    Round price to exchange tick size.
    
    Args:
        price: Price to round
        tick_size: Minimum price increment
        
    Returns:
        Rounded price
    """
    return round(price / tick_size) * tick_size


def calculate_pnl(entry_price: float, exit_price: float, position_size: float, 
                 side: str, leverage: int = 1) -> float:
    """
    Calculate profit and loss for a position.
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        position_size: Position size
        side: 'long' or 'short'
        leverage: Leverage multiplier
        
    Returns:
        PnL amount
    """
    if side.lower() == 'long':
        pnl = (exit_price - entry_price) * position_size * leverage
    else:  # short
        pnl = (entry_price - exit_price) * position_size * leverage
    
    return pnl


def calculate_pnl_percentage(entry_price: float, exit_price: float, side: str, leverage: int = 1) -> float:
    """
    Calculate PnL as percentage.
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        side: 'long' or 'short'
        leverage: Leverage multiplier
        
    Returns:
        PnL percentage
    """
    if side.lower() == 'long':
        pnl_pct = ((exit_price - entry_price) / entry_price) * leverage
    else:  # short
        pnl_pct = ((entry_price - exit_price) / entry_price) * leverage
    
    return pnl_pct
