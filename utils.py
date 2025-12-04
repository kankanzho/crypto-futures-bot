"""
Utility functions for the crypto futures bot.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = 'config/config.yaml') -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def setup_logging(config: Dict[str, Any]):
    """
    Setup logging based on configuration.
    
    Args:
        config: Configuration dictionary
    """
    import logging
    from pathlib import Path
    
    log_config = config.get('logging', {})
    level = getattr(logging, log_config.get('level', 'INFO'))
    format_str = log_config.get('format', '[%(asctime)s] %(levelname)s - %(message)s')
    datefmt = log_config.get('datefmt', '%Y-%m-%d %H:%M:%S')
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt=datefmt
    )
    
    # Add file handler if specified
    log_file = log_config.get('file')
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(format_str, datefmt))
        
        logging.getLogger().addHandler(file_handler)
