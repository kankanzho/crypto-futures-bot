"""
Main Entry Point for Crypto Futures Bot

Demonstrates the auto-strategy switching system.
"""

import logging
import time
import signal
import sys
from pathlib import Path

from utils import load_config, setup_logging
from core import AutoStrategyManager
from mock_bot import MockBot


# Global flag for graceful shutdown
running = True


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global running
    print("\n\nShutdown signal received. Stopping...")
    running = False


def main():
    """Main entry point."""
    global running
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load configuration
    print("Loading configuration...")
    try:
        config = load_config('config/config.yaml')
    except FileNotFoundError:
        print("ERROR: config/config.yaml not found!")
        print("Please create a configuration file based on config/config.yaml.example")
        return 1
    except Exception as e:
        print(f"ERROR loading configuration: {e}")
        return 1
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("Crypto Futures Bot - Auto Strategy Switching System")
    logger.info("=" * 70)
    
    # Check if auto-switching is enabled
    auto_config = config.get('auto_strategy_switching', {})
    if not auto_config.get('enabled', False):
        logger.warning("Auto-strategy switching is disabled in config!")
        logger.warning("Set 'auto_strategy_switching.enabled: true' to enable")
        return 1
    
    # Show configuration
    logger.info("Configuration:")
    logger.info(f"  Dry Run Mode: {auto_config.get('dry_run', False)}")
    logger.info(f"  Check Interval: {auto_config.get('check_interval', 300)}s")
    logger.info(f"  Min Strategy Duration: {auto_config.get('min_strategy_duration', 1800)}s")
    logger.info(f"  Score Threshold: {auto_config.get('score_threshold', 70)}")
    logger.info("")
    
    # Create bot instance
    logger.info("Initializing trading bot...")
    bot = MockBot(initial_strategy='combined')
    
    # Create auto-strategy manager
    logger.info("Initializing auto-strategy manager...")
    auto_manager = AutoStrategyManager(bot, config)
    
    # Start auto-switching
    logger.info("Starting auto-strategy switching...")
    auto_manager.start()
    
    logger.info("")
    logger.info("System is running. Press Ctrl+C to stop.")
    logger.info("=" * 70)
    logger.info("")
    
    # Main loop
    try:
        while running:
            time.sleep(1)
            
            # Periodically show status
            if int(time.time()) % 60 == 0:  # Every minute
                stats = auto_manager.get_statistics()
                logger.info(
                    f"Status: Strategy={stats['current_strategy']}, "
                    f"Duration={stats['strategy_duration_minutes']:.1f}min, "
                    f"Total Switches={stats['total_switches']}"
                )
    
    except KeyboardInterrupt:
        logger.info("\nKeyboardInterrupt received")
    
    finally:
        # Cleanup
        logger.info("Stopping auto-strategy manager...")
        auto_manager.stop()
        
        # Show final statistics
        logger.info("")
        logger.info("=" * 70)
        logger.info("Final Statistics:")
        stats = auto_manager.get_statistics()
        logger.info(f"  Total Switches: {stats['total_switches']}")
        logger.info(f"  Final Strategy: {stats['current_strategy']}")
        
        if stats.get('time_per_strategy'):
            logger.info("  Time per strategy:")
            for strategy, minutes in stats['time_per_strategy'].items():
                logger.info(f"    {strategy}: {minutes:.1f} minutes")
        
        logger.info("=" * 70)
        logger.info("Shutdown complete")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
