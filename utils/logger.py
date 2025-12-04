"""
Logging configuration for the trading bot.
Uses loguru for enhanced logging capabilities.
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional
import os


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "100 MB",
    retention: str = "30 days",
    compression: str = "zip"
) -> None:
    """
    Configure the logger with file and console outputs.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, uses default from env
        rotation: When to rotate log file
        retention: How long to keep old log files
        compression: Compression format for old logs
    """
    # Remove default handler
    logger.remove()
    
    # Get log level from environment or use default
    level = os.getenv("LOG_LEVEL", log_level).upper()
    
    # Add console handler with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # Add file handler if log file specified
    if log_file is None:
        log_file = os.getenv("LOG_FILE", "logs/trading_bot.log")
    
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8"
    )
    
    logger.info(f"Logger initialized with level: {level}")
    logger.info(f"Log file: {log_file}")


def get_logger():
    """
    Get the configured logger instance.
    
    Returns:
        logger: Configured logger instance
    """
    return logger


# Initialize logger on module import
setup_logger()
