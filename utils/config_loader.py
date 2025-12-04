"""
Configuration loader utility.
Loads and manages configuration from YAML files.
"""

from pathlib import Path
from typing import Any, Dict
import yaml
from utils.logger import get_logger

logger = get_logger()


class ConfigLoader:
    """Handles loading and accessing configuration files."""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config: Dict[str, Any] = {}
        self.strategy_params: Dict[str, Any] = {}
        self.coins: list = []
        
        self._load_all_configs()
    
    def _load_all_configs(self) -> None:
        """Load all configuration files."""
        try:
            # Load main config
            config_path = self.config_dir / "config.yaml"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Loaded main configuration from {config_path}")
            else:
                logger.warning(f"Main config file not found: {config_path}")
            
            # Load strategy parameters
            strategy_path = self.config_dir / "strategy_params.yaml"
            if strategy_path.exists():
                with open(strategy_path, 'r') as f:
                    self.strategy_params = yaml.safe_load(f) or {}
                logger.info(f"Loaded strategy parameters from {strategy_path}")
            else:
                logger.warning(f"Strategy params file not found: {strategy_path}")
            
            # Load coins configuration
            coins_path = self.config_dir / "coins.yaml"
            if coins_path.exists():
                with open(coins_path, 'r') as f:
                    data = yaml.safe_load(f) or {}
                    self.coins = data.get('coins', [])
                logger.info(f"Loaded {len(self.coins)} coins from {coins_path}")
            else:
                logger.warning(f"Coins config file not found: {coins_path}")
                
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'trading.leverage')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_strategy_params(self, strategy: str) -> Dict[str, Any]:
        """
        Get parameters for a specific strategy.
        
        Args:
            strategy: Strategy name
            
        Returns:
            Dictionary of strategy parameters
        """
        return self.strategy_params.get(strategy, {})
    
    def get_enabled_coins(self) -> list:
        """
        Get list of enabled coins for trading.
        
        Returns:
            List of enabled coin configurations
        """
        return [coin for coin in self.coins if coin.get('enabled', False)]
    
    def get_coin_config(self, symbol: str) -> Dict[str, Any]:
        """
        Get configuration for a specific coin.
        
        Args:
            symbol: Coin symbol (e.g., 'BTCUSDT')
            
        Returns:
            Coin configuration dictionary or empty dict if not found
        """
        for coin in self.coins:
            if coin.get('symbol') == symbol:
                return coin
        return {}
    
    def reload(self) -> None:
        """Reload all configuration files."""
        logger.info("Reloading configuration files")
        self._load_all_configs()


# Global configuration instance
_config_instance = None


def get_config() -> ConfigLoader:
    """
    Get the global configuration instance.
    
    Returns:
        ConfigLoader instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance
