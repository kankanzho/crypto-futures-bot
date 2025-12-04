"""
Main trading bot execution file.
Coordinates all components and manages trading across multiple coins.
"""

import asyncio
import signal
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from utils.logger import setup_logger
from utils.helpers import (
    load_config, load_strategy_config, load_env_config,
    validate_api_credentials, ensure_directories
)
from exchange import BybitClient, MarketDataManager
from strategies import RSIStrategy, MACDStrategy, BollingerStrategy, EMACrossStrategy
from risk_management import StopLossManager, TakeProfitManager, PositionSizer


class TradingBot:
    """Main trading bot class."""
    
    def __init__(self, config_path: str = "config/config.yaml",
                 strategy_config_path: str = "config/strategies.yaml"):
        """
        Initialize trading bot.
        
        Args:
            config_path: Path to main configuration file
            strategy_config_path: Path to strategy configuration file
        """
        # Setup logger
        setup_logger(config_path)
        
        # Load configurations
        self.config = load_config(config_path)
        self.strategy_config = load_strategy_config(strategy_config_path)
        self.env_config = load_env_config()
        
        # Validate API credentials
        if not validate_api_credentials(
            self.env_config['api_key'],
            self.env_config['api_secret']
        ):
            logger.error("Invalid API credentials. Please check your .env file.")
            sys.exit(1)
        
        # Ensure directories exist
        ensure_directories()
        
        # Initialize components
        self.client: Optional[BybitClient] = None
        self.market_data: Optional[MarketDataManager] = None
        self.strategies: Dict[str, Any] = {}
        self.active_coins: List[str] = []
        
        # Trading state
        self.is_running = False
        self.positions: Dict[str, Dict] = {}
        self.daily_pnl: float = 0
        self.weekly_pnl: float = 0
        
        # Performance tracking
        self.trade_history: List[Dict] = []
        self.equity_curve: List[float] = []
        
        logger.info("Trading bot initialized")
    
    def initialize(self):
        """Initialize all bot components."""
        logger.info("Initializing bot components...")
        
        # Initialize Bybit client
        self.client = BybitClient(
            api_key=self.env_config['api_key'],
            api_secret=self.env_config['api_secret'],
            testnet=self.env_config['testnet'],
            rate_limit_config=self.config['api']['rate_limit']
        )
        
        # Initialize market data manager
        self.market_data = MarketDataManager(
            testnet=self.env_config['testnet']
        )
        
        # Load active coins
        self.active_coins = [
            coin['symbol'] for coin in self.config['trading']['coins']
            if coin.get('enabled', True)
        ]
        
        logger.info(f"Active coins: {self.active_coins}")
        
        # Initialize strategy for the bot
        self._initialize_strategy()
        
        # Set leverage for each coin
        for coin_config in self.config['trading']['coins']:
            if coin_config.get('enabled', True):
                symbol = coin_config['symbol']
                leverage = coin_config['leverage']
                try:
                    self.client.set_leverage(symbol, leverage, leverage)
                    logger.info(f"Leverage set for {symbol}: {leverage}x")
                except Exception as e:
                    logger.error(f"Failed to set leverage for {symbol}: {e}")
        
        logger.info("Bot components initialized successfully")
    
    def _initialize_strategy(self):
        """Initialize trading strategy based on configuration."""
        # Get active strategy from config (default to RSI)
        active_strategy = "rsi"  # Can be made configurable
        
        # Map strategy names to classes
        strategy_map = {
            'rsi': RSIStrategy,
            'macd': MACDStrategy,
            'bollinger': BollingerStrategy,
            'ema_cross': EMACrossStrategy
        }
        
        # Initialize strategy
        if active_strategy in strategy_map and active_strategy in self.strategy_config:
            strategy_class = strategy_map[active_strategy]
            strategy_params = self.strategy_config[active_strategy]['parameters']
            
            self.strategy = strategy_class(strategy_params)
            
            # Initialize risk management for strategy
            sl_config = self.strategy_config[active_strategy]['stop_loss']
            tp_config = self.strategy_config[active_strategy]['take_profit']
            
            self.stop_loss_manager = StopLossManager(sl_config)
            self.take_profit_manager = TakeProfitManager(tp_config)
            self.position_sizer = PositionSizer(self.config['trading']['position_sizing'])
            
            logger.info(f"Strategy initialized: {self.strategy.name}")
        else:
            logger.error(f"Strategy not found: {active_strategy}")
            sys.exit(1)
    
    async def start(self):
        """Start the trading bot."""
        logger.info("Starting trading bot...")
        self.is_running = True
        
        # Subscribe to market data
        timeframes = [
            self.config['trading']['timeframes']['primary'],
            self.config['trading']['timeframes']['secondary']
        ]
        
        await self.market_data.subscribe_klines(self.active_coins, timeframes)
        
        # Start main trading loop
        try:
            await self._trading_loop()
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            await self.stop()
    
    async def _trading_loop(self):
        """Main trading loop."""
        logger.info("Trading loop started")
        
        while self.is_running:
            try:
                # Check risk limits
                if not self._check_risk_limits():
                    logger.warning("Risk limits exceeded, pausing trading")
                    await asyncio.sleep(60)
                    continue
                
                # Process each coin
                for symbol in self.active_coins:
                    await self._process_symbol(symbol)
                
                # Update performance metrics
                self._update_metrics()
                
                # Wait before next iteration
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in trading loop iteration: {e}")
                await asyncio.sleep(10)
    
    async def _process_symbol(self, symbol: str):
        """
        Process trading logic for a symbol.
        
        Args:
            symbol: Trading pair symbol
        """
        try:
            # Get market data
            timeframe = self.config['trading']['timeframes']['primary']
            klines = self.client.get_kline(symbol, timeframe, limit=200)
            
            if not klines:
                return
            
            # Convert to DataFrame
            df = self._klines_to_dataframe(klines)
            
            # Generate signal
            signal = self.strategy.generate_signal(symbol, df)
            
            # Check for entry
            if self.strategy.should_enter_long(symbol, df):
                await self._enter_position(symbol, 'long', df)
            elif self.strategy.should_enter_short(symbol, df):
                await self._enter_position(symbol, 'short', df)
            
            # Check for exit
            if self.strategy.should_exit_long(symbol, df):
                await self._exit_position(symbol)
            elif self.strategy.should_exit_short(symbol, df):
                await self._exit_position(symbol)
            
            # Update stops for open positions
            if symbol in self.positions:
                await self._update_position_management(symbol, df)
                
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    
    async def _enter_position(self, symbol: str, side: str, market_data: pd.DataFrame):
        """
        Enter a new position.
        
        Args:
            symbol: Trading pair symbol
            side: 'long' or 'short'
            market_data: Market data DataFrame
        """
        try:
            # Check if already in position
            if symbol in self.positions:
                logger.debug(f"Already in position for {symbol}")
                return
            
            # Get current price
            ticker = self.client.get_ticker(symbol)
            current_price = float(ticker.get('lastPrice', 0))
            
            if current_price == 0:
                logger.error(f"Invalid price for {symbol}")
                return
            
            # Calculate stop loss
            stop_loss = self.stop_loss_manager.calculate_stop_loss(
                current_price, side, market_data
            )
            
            # Calculate position size
            capital = self._get_available_capital(symbol)
            position_size = self.position_sizer.calculate_position_size(
                capital, current_price, stop_loss,
                self._get_leverage(symbol)
            )
            
            # Validate position size
            position_size = self.position_sizer.validate_position_size(
                position_size, current_price, capital,
                self._get_leverage(symbol)
            )
            
            if position_size <= 0:
                logger.warning(f"Invalid position size for {symbol}")
                return
            
            # Calculate take profit
            tp_levels = self.take_profit_manager.calculate_take_profit(
                current_price, stop_loss, side, market_data
            )
            
            # Place order
            order_side = 'Buy' if side == 'long' else 'Sell'
            
            order = self.client.place_order(
                symbol=symbol,
                side=order_side,
                order_type='Market',
                qty=position_size,
                stop_loss=stop_loss,
                take_profit=tp_levels[0][0] if tp_levels else None
            )
            
            if order:
                # Update position tracking
                self.positions[symbol] = {
                    'side': side,
                    'size': position_size,
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': tp_levels,
                    'entry_time': datetime.now()
                }
                
                # Update strategy
                self.strategy.update_position(symbol, side, position_size, current_price)
                
                # Set risk management
                self.stop_loss_manager.set_stop_loss(symbol, current_price, side, market_data)
                self.take_profit_manager.set_take_profit(symbol, current_price, stop_loss, side, market_data)
                
                logger.info(f"Position entered: {symbol} {side} {position_size} @ {current_price}")
                
        except Exception as e:
            logger.error(f"Error entering position for {symbol}: {e}")
    
    async def _exit_position(self, symbol: str):
        """
        Exit a position.
        
        Args:
            symbol: Trading pair symbol
        """
        try:
            if symbol not in self.positions:
                return
            
            # Close position
            result = self.client.close_position(symbol)
            
            if result:
                position = self.positions[symbol]
                
                # Record trade
                self.trade_history.append({
                    'symbol': symbol,
                    'side': position['side'],
                    'entry_price': position['entry_price'],
                    'entry_time': position['entry_time'],
                    'exit_time': datetime.now(),
                    'size': position['size']
                })
                
                # Clean up
                del self.positions[symbol]
                self.strategy.close_position(symbol)
                self.stop_loss_manager.remove_stop_loss(symbol)
                self.take_profit_manager.remove_take_profit(symbol)
                
                logger.info(f"Position exited: {symbol}")
                
        except Exception as e:
            logger.error(f"Error exiting position for {symbol}: {e}")
    
    async def _update_position_management(self, symbol: str, market_data: pd.DataFrame):
        """Update stop loss and take profit for open position."""
        try:
            current_price = market_data.iloc[-1]['close']
            
            # Update trailing stop if configured
            self.stop_loss_manager.update_stop_loss(symbol, current_price)
            
            # Check if stop or TP hit
            if self.stop_loss_manager.check_stop_hit(symbol, current_price):
                await self._exit_position(symbol)
            elif self.take_profit_manager.check_take_profit_hit(symbol, current_price):
                await self._exit_position(symbol)
                
        except Exception as e:
            logger.error(f"Error updating position management for {symbol}: {e}")
    
    def _klines_to_dataframe(self, klines: List) -> pd.DataFrame:
        """Convert kline data to DataFrame."""
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])
        
        # Convert to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def _get_available_capital(self, symbol: str) -> float:
        """Get available capital for a symbol."""
        # Get wallet balance
        wallet = self.client.get_wallet_balance()
        
        # Calculate allocation
        coin_config = next(
            (c for c in self.config['trading']['coins'] if c['symbol'] == symbol),
            None
        )
        
        if coin_config:
            allocation = coin_config['allocation']
            total_balance = float(wallet.get('result', {}).get('list', [{}])[0].get('totalEquity', 0))
            return total_balance * allocation
        
        return 0
    
    def _get_leverage(self, symbol: str) -> int:
        """Get leverage for a symbol."""
        coin_config = next(
            (c for c in self.config['trading']['coins'] if c['symbol'] == symbol),
            None
        )
        return coin_config['leverage'] if coin_config else 1
    
    def _check_risk_limits(self) -> bool:
        """Check if risk limits are within acceptable range."""
        config = self.config['trading']['risk_management']
        
        # Check daily loss
        if abs(self.daily_pnl) > config['max_daily_loss']:
            logger.warning("Daily loss limit reached")
            return False
        
        # Check weekly loss
        if abs(self.weekly_pnl) > config['max_weekly_loss']:
            logger.warning("Weekly loss limit reached")
            return False
        
        return True
    
    def _update_metrics(self):
        """Update performance metrics."""
        # This would calculate PnL from open positions and closed trades
        # For now, just log
        logger.debug(f"Open positions: {len(self.positions)}")
    
    async def stop(self):
        """Stop the trading bot."""
        logger.info("Stopping trading bot...")
        self.is_running = False
        
        # Close all positions
        for symbol in list(self.positions.keys()):
            await self._exit_position(symbol)
        
        # Shutdown market data
        if self.market_data:
            await self.market_data.shutdown()
        
        logger.info("Trading bot stopped")
    
    def emergency_stop(self):
        """Emergency stop - close all positions immediately."""
        logger.critical("EMERGENCY STOP ACTIVATED")
        
        for symbol in list(self.positions.keys()):
            try:
                self.client.close_position(symbol)
                logger.info(f"Emergency close: {symbol}")
            except Exception as e:
                logger.error(f"Failed to emergency close {symbol}: {e}")
        
        self.is_running = False


async def main():
    """Main entry point."""
    bot = TradingBot()
    bot.initialize()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        asyncio.create_task(bot.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start bot
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
