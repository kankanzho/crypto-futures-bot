"""
Main entry point for the cryptocurrency futures trading bot.
"""

import sys
import argparse
from core.bot import TradingBot
from utils.logger import setup_logger, get_logger
from utils.config_loader import get_config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logger
setup_logger()
logger = get_logger()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Bybit Cryptocurrency Futures Trading Bot')
    
    parser.add_argument(
        '--testnet',
        action='store_true',
        default=True,
        help='Use Bybit testnet (default: True)'
    )
    
    parser.add_argument(
        '--mainnet',
        action='store_true',
        help='Use Bybit mainnet (REAL MONEY - use with caution!)'
    )
    
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Launch with GUI (not yet implemented)'
    )
    
    parser.add_argument(
        '--backtest',
        action='store_true',
        help='Run in backtest mode'
    )
    
    args = parser.parse_args()
    
    # Determine testnet vs mainnet
    use_testnet = not args.mainnet
    
    if not use_testnet:
        logger.warning("=" * 60)
        logger.warning("WARNING: Running on MAINNET with REAL MONEY!")
        logger.warning("=" * 60)
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Exiting...")
            sys.exit(0)
    
    try:
        if args.gui:
            logger.info("Launching GUI...")
            # Import GUI here to avoid import if not needed
            try:
                from gui.main_window import launch_gui
                launch_gui(testnet=use_testnet)
            except ImportError as e:
                logger.error(f"GUI not available: {e}")
                logger.error("Please install PyQt5: pip install PyQt5")
                sys.exit(1)
        
        elif args.backtest:
            logger.info("Running backtest...")
            run_backtest()
        
        else:
            logger.info("Starting trading bot...")
            logger.info(f"Mode: {'TESTNET' if use_testnet else 'MAINNET'}")
            
            # Create and start bot
            bot = TradingBot(testnet=use_testnet)
            
            # Display startup information
            config = get_config()
            logger.info("=" * 60)
            logger.info("Configuration:")
            logger.info(f"  Strategy: {config.get('strategies.active_strategy', 'scalping')}")
            logger.info(f"  Leverage: {config.get('trading.leverage', 10)}x")
            logger.info(f"  Max Positions: {config.get('trading.max_positions', 4)}")
            logger.info(f"  Stop Loss: {config.get('risk_management.stop_loss_pct', 2.0)}%")
            logger.info(f"  Take Profit: {config.get('risk_management.take_profit_pct', 3.0)}%")
            logger.info("=" * 60)
            
            # Show enabled coins
            enabled_coins = config.get_enabled_coins()
            logger.info(f"Trading {len(enabled_coins)} coins:")
            for coin in enabled_coins:
                logger.info(f"  - {coin['symbol']}")
            logger.info("=" * 60)
            
            # Start bot
            bot.start()
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_backtest():
    """Run backtesting."""
    from backtesting.data_loader import DataLoader
    from backtesting.backtest_engine import BacktestEngine
    from backtesting.performance_analyzer import PerformanceAnalyzer
    from strategies.scalping_strategy import ScalpingStrategy
    from strategies.rsi_strategy import RSIStrategy
    from strategies.macd_strategy import MACDStrategy
    from utils.config_loader import get_config
    
    config = get_config()
    
    # Get backtest configuration
    start_date = config.get('backtesting.start_date', '2024-01-01')
    end_date = config.get('backtesting.end_date', '2024-12-01')
    initial_capital = config.get('backtesting.initial_capital', 10000)
    
    # Load data
    logger.info("Loading historical data...")
    loader = DataLoader(testnet=True)
    
    df = loader.load_historical_data(
        symbol='BTCUSDT',
        interval='1',
        start_date=start_date,
        end_date=end_date
    )
    
    if df.empty:
        logger.error("No data loaded. Exiting backtest.")
        return
    
    # Prepare data with indicators
    df = loader.prepare_data_for_strategy(df)
    
    # Test multiple strategies
    strategies = [
        ('Scalping', ScalpingStrategy()),
        ('RSI', RSIStrategy()),
        ('MACD', MACDStrategy())
    ]
    
    logger.info("=" * 80)
    logger.info("BACKTEST RESULTS")
    logger.info("=" * 80)
    
    for name, strategy in strategies:
        logger.info(f"\nTesting {name} Strategy...")
        logger.info("-" * 60)
        
        # Run backtest
        engine = BacktestEngine(
            strategy=strategy,
            initial_capital=initial_capital,
            commission_rate=config.get('backtesting.commission', 0.075),
            slippage=config.get('backtesting.slippage', 0.05)
        )
        
        results = engine.run(df)
        
        # Analyze performance
        analysis = PerformanceAnalyzer.analyze(results, engine.equity_curve)
        
        # Display results
        logger.info(f"Initial Capital: ${analysis['initial_capital']:,.2f}")
        logger.info(f"Final Capital: ${analysis['final_capital']:,.2f}")
        logger.info(f"Total Return: ${analysis['total_return']:,.2f} ({analysis['total_return_pct']:.2f}%)")
        logger.info(f"Total Trades: {analysis['total_trades']}")
        logger.info(f"Winning Trades: {analysis['winning_trades']}")
        logger.info(f"Losing Trades: {analysis['losing_trades']}")
        logger.info(f"Win Rate: {analysis['win_rate']:.2f}%")
        logger.info(f"Average Win: ${analysis['avg_win']:.2f}")
        logger.info(f"Average Loss: ${analysis['avg_loss']:.2f}")
        logger.info(f"Profit Factor: {analysis['profit_factor']:.2f}")
        logger.info(f"Max Drawdown: {analysis['max_drawdown_pct']:.2f}%")
        logger.info("-" * 60)
    
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
