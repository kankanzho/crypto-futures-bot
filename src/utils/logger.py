"""
Logging utility for the crypto futures bot.
Uses loguru for enhanced logging capabilities.
"""

import sys
from pathlib import Path
from loguru import logger
import yaml


def setup_logger(config_path: str = "config/config.yaml"):
    """
    Setup logger with configuration from config file.
    
    Args:
        config_path: Path to configuration file
    """
    # Remove default handler
    logger.remove()
    
    # Load configuration
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            log_config = config.get('logging', {})
    except Exception:
        # Use defaults if config not found
        log_config = {
            'level': 'INFO',
            'log_to_file': True,
            'log_rotation': '1 day',
            'log_retention': '30 days'
        }
    
    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_config.get('level', 'INFO'),
        colorize=True
    )
    
    # File handler
    if log_config.get('log_to_file', True):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logger.add(
            "logs/bot_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_config.get('level', 'INFO'),
            rotation=log_config.get('log_rotation', '1 day'),
            retention=log_config.get('log_retention', '30 days'),
            compression="zip"
        )
        
        # Separate file for errors
        logger.add(
            "logs/error_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation=log_config.get('log_rotation', '1 day'),
            retention=log_config.get('log_retention', '30 days'),
            compression="zip"
        )
    
    logger.info("Logger initialized successfully")
    return logger


def get_logger():
    """Get the configured logger instance."""
    return logger
