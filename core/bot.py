"""
Main trading bot logic.
Coordinates all components for live trading.
"""

import pandas as pd
from typing import Dict, Optional
import time
from datetime import datetime
from core.bybit_api import BybitAPI
from core.websocket_client import BybitWebSocket
from core.order_manager import OrderManager
from core.position_manager import PositionManager
from core.risk_manager import RiskManager
from strategies.base_strategy import BaseStrategy
from strategies.scalping_strategy import ScalpingStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.ema_cross_strategy import EMACrossStrategy
from strategies.strategy_combiner import StrategyCombiner
from indicators.technical_indicators import calculate_all_indicators
from utils.logger import get_logger
from utils.config_loader import get_config
from utils.notifications import get_notification_manager

logger = get_logger()


class TradingBot:
    """Main trading bot coordinator."""
    
    def __init__(self, testnet: bool = True):
        """
        Initialize trading bot.
        
        Args:
            testnet: Whether to use testnet
        """
        self.testnet = testnet
        self.running = False
        
        # Load configuration
        self.config = get_config()
        
        # Initialize components
        self.api = BybitAPI(testnet=testnet)
        self.websocket = BybitWebSocket(testnet=testnet)
        self.order_manager = OrderManager(self.api)
        self.position_manager = PositionManager()
        
        # Get initial capital from wallet
        initial_capital = self._get_wallet_balance()
        self.risk_manager = RiskManager(initial_capital)
        
        # Initialize notification manager
        self.notification_manager = get_notification_manager(
            enable_sound=self.config.get('notification.enable_sound', True),
            enable_popup=self.config.get('notification.enable_popup', True)
        )
        
        # Initialize strategy
        self.strategy = self._create_strategy()
        
        # Data storage for each symbol
        self.market_data: Dict[str, pd.DataFrame] = {}
        
        logger.info(f"Trading Bot initialized (Testnet: {testnet})")
    
    def _get_wallet_balance(self) -> float:
        """Get wallet balance from exchange."""
        try:
            wallet = self.api.get_wallet_balance()
            if wallet and 'list' in wallet:
                for account in wallet['list']:
                    if 'coin' in account:
                        for coin in account['coin']:
                            if coin.get('coin') == 'USDT':
                                balance = float(coin.get('walletBalance', 10000))
                                logger.info(f"Wallet balance: ${balance:.2f}")
                                return balance
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}")
        
        # Default fallback
        return 10000.0
    
    def _create_strategy(self) -> BaseStrategy:
        """Create strategy based on configuration."""
        strategy_name = self.config.get('strategies.active_strategy', 'scalping')
        
        strategies = {
            'scalping': ScalpingStrategy,
            'rsi': RSIStrategy,
            'macd': MACDStrategy,
            'bollinger': BollingerStrategy,
            'momentum': MomentumStrategy,
            'ema_cross': EMACrossStrategy,
            'combined': StrategyCombiner
        }
        
        strategy_class = strategies.get(strategy_name, ScalpingStrategy)
        strategy = strategy_class()
        
        logger.info(f"Strategy selected: {strategy_name}")
        
        return strategy
    
    def start(self) -> None:
        """Start the trading bot."""
        if self.running:
            logger.warning("Bot is already running")
            return
        
        logger.info("Starting trading bot...")
        
        self.running = True
        
        # Get enabled coins
        enabled_coins = self.config.get_enabled_coins()
        
        if not enabled_coins:
            logger.error("No enabled coins found in configuration")
            return
        
        # Set leverage for each coin
        leverage = self.config.get('trading.leverage', 10)
        for coin in enabled_coins:
            symbol = coin['symbol']
            self.api.set_leverage(symbol, leverage, leverage)
        
        # Connect WebSocket
        self.websocket.connect()
        
        # Main trading loop
        try:
            self._run_trading_loop(enabled_coins)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
        finally:
            self.stop()
    
    def _run_trading_loop(self, coins: list) -> None:
        """Main trading loop."""
        interval = self.config.get_strategy_params(self.strategy.name).get('timeframe', '1')
        
        while self.running:
            try:
                # Update daily P&L tracking
                self.risk_manager.reset_daily_pnl()
                
                # Process each coin
                for coin in coins:
                    symbol = coin['symbol']
                    
                    # Fetch latest data
                    self._update_market_data(symbol, interval)
                    
                    # Process trading logic
                    self._process_symbol(symbol)
                
                # Update positions
                self._update_positions()
                
                # Sleep before next iteration
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in trading loop iteration: {e}")
                time.sleep(5)
    
    def _update_market_data(self, symbol: str, interval: str) -> None:
        """Update market data for a symbol."""
        try:
            # Fetch recent klines
            klines = self.api.get_kline(symbol=symbol, interval=interval, limit=100)
            
            if not klines:
                return
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            
            # Convert types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            # Sort and calculate indicators
            df = df.sort_values('timestamp').reset_index(drop=True)
            df = calculate_all_indicators(df)
            
            # Store
            self.market_data[symbol] = df
            
        except Exception as e:
            logger.error(f"Error updating market data for {symbol}: {e}")
    
    def _process_symbol(self, symbol: str) -> None:
        """Process trading logic for a symbol."""
        try:
            # Check if we have data
            if symbol not in self.market_data:
                return
            
            df = self.market_data[symbol]
            
            if df.empty or len(df) < 50:
                return
            
            # Get current price
            current_price = float(df['close'].iloc[-1])
            
            # Check if we have a position
            has_position = self.position_manager.has_position(symbol)
            
            if has_position:
                # Manage existing position
                self._manage_position(symbol, current_price, df)
            else:
                # Look for entry signal
                self._check_entry_signal(symbol, current_price, df)
                
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    
    def _check_entry_signal(self, symbol: str, current_price: float, df: pd.DataFrame) -> None:
        """Check for entry signals."""
        # Generate signal
        signal = self.strategy.generate_signal(df)
        
        if signal.is_neutral():
            return
        
        # Check if should enter
        if not self.strategy.should_enter_trade(signal, df):
            return
        
        # Calculate stop loss and take profit
        side = 'long' if signal.is_long() else 'short'
        
        stop_loss = self.risk_manager.calculate_stop_loss(
            entry_price=current_price,
            side=side
        )
        
        take_profit = self.risk_manager.calculate_take_profit(
            entry_price=current_price,
            side=side,
            stop_loss_price=stop_loss
        )
        
        # Calculate position size
        position_info = self.risk_manager.calculate_position_size(
            entry_price=current_price,
            stop_loss_price=stop_loss,
            symbol=symbol
        )
        
        quantity = position_info['quantity']
        
        # Validate order
        order_side = 'Buy' if side == 'long' else 'Sell'
        valid, reason = self.risk_manager.validate_order(symbol, order_side, quantity, current_price)
        
        if not valid:
            logger.warning(f"Order validation failed: {reason}")
            return
        
        # Place order
        logger.info(f"Entering {side} position: {symbol} @ {current_price}")
        
        order = self.order_manager.create_market_order(
            symbol=symbol,
            side=order_side,
            quantity=quantity
        )
        
        if order:
            # Add position
            self.position_manager.add_position(
                symbol=symbol,
                side=side,
                entry_price=current_price,
                quantity=quantity,
                leverage=self.config.get('trading.leverage', 10),
                stop_loss=stop_loss,
                take_profit=take_profit,
                order_id=order.order_id
            )
            
            # Update risk manager
            self.risk_manager.open_positions_count += 1
            
            # Notify
            self.notification_manager.notify_trade_entry(
                symbol=symbol,
                side=side,
                price=current_price,
                quantity=quantity
            )
    
    def _manage_position(self, symbol: str, current_price: float, df: pd.DataFrame) -> None:
        """Manage existing position."""
        position = self.position_manager.get_position(symbol)
        
        if not position:
            return
        
        # Update position P&L
        position.update_pnl(current_price)
        
        # Check stop loss
        if self.position_manager.check_stop_loss(symbol, current_price):
            logger.info(f"Stop loss hit for {symbol}")
            self._close_position(symbol, current_price, "stop_loss")
            return
        
        # Check take profit
        if self.position_manager.check_take_profit(symbol, current_price):
            logger.info(f"Take profit hit for {symbol}")
            self._close_position(symbol, current_price, "take_profit")
            return
        
        # Update trailing stop if enabled
        if self.config.get('risk_management.trailing_stop', False):
            new_stop = self.risk_manager.update_trailing_stop(
                entry_price=position.entry_price,
                current_price=current_price,
                current_stop=position.stop_loss,
                side=position.side
            )
            position.stop_loss = new_stop
    
    def _close_position(self, symbol: str, exit_price: float, reason: str) -> None:
        """Close a position."""
        position = self.position_manager.get_position(symbol)
        
        if not position:
            return
        
        # Place closing order
        close_side = 'Sell' if position.side == 'long' else 'Buy'
        
        order = self.order_manager.create_market_order(
            symbol=symbol,
            side=close_side,
            quantity=position.quantity,
            reduce_only=True
        )
        
        if order:
            # Close position in manager
            closed_position = self.position_manager.close_position(symbol, exit_price, reason)
            
            if closed_position:
                # Update risk manager
                self.risk_manager.open_positions_count -= 1
                self.risk_manager.add_trade_pnl(closed_position.realized_pnl)
                
                # Notify
                pnl_pct = closed_position.get_pnl_percentage(exit_price)
                self.notification_manager.notify_trade_exit(
                    symbol=symbol,
                    side=position.side,
                    price=exit_price,
                    quantity=position.quantity,
                    pnl=closed_position.realized_pnl,
                    pnl_pct=pnl_pct
                )
    
    def _update_positions(self) -> None:
        """Update all positions with latest prices."""
        # Sync orders with exchange
        self.order_manager.sync_orders()
        
        # Update capital
        balance = self._get_wallet_balance()
        self.risk_manager.update_capital(balance)
    
    def stop(self) -> None:
        """Stop the trading bot."""
        if not self.running:
            return
        
        logger.info("Stopping trading bot...")
        
        self.running = False
        
        # Disconnect WebSocket
        self.websocket.disconnect()
        
        logger.info("Trading bot stopped")
    
    def emergency_close_all(self) -> None:
        """Emergency close all positions."""
        logger.warning("Emergency closing all positions!")
        
        positions = self.position_manager.get_all_positions()
        
        for position in positions:
            try:
                current_price = float(self.market_data.get(position.symbol, pd.DataFrame()).get('close', [0]).iloc[-1])
                if current_price > 0:
                    self._close_position(position.symbol, current_price, "emergency")
            except Exception as e:
                logger.error(f"Error closing position {position.symbol}: {e}")
