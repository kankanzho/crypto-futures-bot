"""
Backtest engine for testing trading strategies on historical data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from ..strategies.base_strategy import BaseStrategy, SignalType
from ..risk_management import StopLossManager, TakeProfitManager, PositionSizer
from .performance_metrics import PerformanceMetrics


class Trade:
    """Represents a single trade."""
    
    def __init__(self, symbol: str, side: str, entry_time: datetime, entry_price: float,
                 size: float, stop_loss: float, take_profit: List[tuple]):
        self.symbol = symbol
        self.side = side
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.size = size
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        
        self.exit_time: Optional[datetime] = None
        self.exit_price: Optional[float] = None
        self.pnl: float = 0
        self.pnl_percent: float = 0
        self.exit_reason: str = ""
        self.remaining_size: float = size
    
    def close(self, exit_time: datetime, exit_price: float, size: float, reason: str):
        """Close the trade (fully or partially)."""
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_reason = reason
        
        # Calculate PnL for this exit
        if self.side == 'long':
            pnl = (exit_price - self.entry_price) * size
        else:  # short
            pnl = (self.entry_price - exit_price) * size
        
        self.pnl += pnl
        self.remaining_size -= size
        
        # Calculate percentage (based on entry value)
        self.pnl_percent = (self.pnl / (self.entry_price * self.size)) * 100
    
    def is_closed(self) -> bool:
        """Check if trade is fully closed."""
        return self.remaining_size <= 0.0001  # Account for floating point


class BacktestEngine:
    """Backtesting engine for strategy evaluation."""
    
    def __init__(self, strategy: BaseStrategy, initial_capital: float,
                 commission: float = 0.0006, slippage: float = 0.0005,
                 leverage: int = 1):
        """
        Initialize backtest engine.
        
        Args:
            strategy: Trading strategy to test
            initial_capital: Initial capital
            commission: Commission rate (e.g., 0.0006 for 0.06%)
            slippage: Estimated slippage (e.g., 0.0005 for 0.05%)
            leverage: Leverage multiplier
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.leverage = leverage
        
        self.capital = initial_capital
        self.trades: List[Trade] = []
        self.open_trades: Dict[str, Trade] = {}
        self.equity_curve: List[float] = [initial_capital]
        self.timestamps: List[datetime] = []
        
        logger.info(f"Backtest engine initialized: {strategy.name}, capital=${initial_capital}")
    
    def run(self, data: Dict[str, pd.DataFrame], 
            stop_loss_config: Dict[str, Any],
            take_profit_config: Dict[str, Any],
            position_size_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run backtest on historical data.
        
        Args:
            data: Dictionary of symbol -> OHLCV DataFrame
            stop_loss_config: Stop loss configuration
            take_profit_config: Take profit configuration
            position_size_config: Position sizing configuration
            
        Returns:
            Backtest results dictionary
        """
        logger.info("Starting backtest...")
        
        # Initialize risk management
        sl_manager = StopLossManager(stop_loss_config)
        tp_manager = TakeProfitManager(take_profit_config)
        position_sizer = PositionSizer(position_size_config)
        
        # Get all timestamps (assuming all symbols have same timestamps)
        first_symbol = list(data.keys())[0]
        timestamps = data[first_symbol].index
        
        # Run through historical data
        for i, timestamp in enumerate(timestamps):
            # Update equity curve
            current_equity = self._calculate_equity(data, i)
            self.equity_curve.append(current_equity)
            self.timestamps.append(timestamp)
            
            # Check open positions
            for symbol in list(self.open_trades.keys()):
                if symbol in data:
                    current_price = data[symbol].iloc[i]['close']
                    self._check_exits(symbol, current_price, timestamp, sl_manager, tp_manager)
            
            # Check for new entries
            for symbol, df in data.items():
                if i < 100:  # Need minimum data for indicators
                    continue
                
                # Get data up to current point
                historical_data = df.iloc[:i+1]
                
                # Generate signal
                signal = self.strategy.generate_signal(symbol, historical_data)
                
                # Enter position if signal generated
                if signal == SignalType.BUY or signal == SignalType.SELL:
                    if symbol not in self.open_trades:
                        self._enter_position(
                            symbol, signal, historical_data, timestamp,
                            sl_manager, tp_manager, position_sizer
                        )
        
        # Close any remaining open positions at end
        for symbol in list(self.open_trades.keys()):
            if symbol in data:
                final_price = data[symbol].iloc[-1]['close']
                final_time = timestamps[-1]
                self._close_position(symbol, final_price, final_time, "backtest_end")
        
        # Calculate performance metrics
        results = self._calculate_results()
        
        logger.info("Backtest completed")
        return results
    
    def _enter_position(self, symbol: str, signal: SignalType, data: pd.DataFrame,
                       timestamp: datetime, sl_manager: StopLossManager,
                       tp_manager: TakeProfitManager, position_sizer: PositionSizer):
        """Enter a new position."""
        current_price = data.iloc[-1]['close']
        side = 'long' if signal == SignalType.BUY else 'short'
        
        # Apply slippage
        if side == 'long':
            entry_price = current_price * (1 + self.slippage)
        else:
            entry_price = current_price * (1 - self.slippage)
        
        # Calculate stop loss
        stop_loss = sl_manager.calculate_stop_loss(entry_price, side, data)
        
        # Calculate position size
        position_size = position_sizer.calculate_position_size(
            self.capital, entry_price, stop_loss, self.leverage
        )
        
        # Validate position size
        position_size = position_sizer.validate_position_size(
            position_size, entry_price, self.capital, self.leverage
        )
        
        if position_size <= 0:
            return
        
        # Calculate take profit levels
        tp_levels = tp_manager.calculate_take_profit(entry_price, stop_loss, side, data)
        
        # Deduct commission
        commission_cost = position_size * entry_price * self.commission
        self.capital -= commission_cost
        
        # Create trade
        trade = Trade(symbol, side, timestamp, entry_price, position_size, stop_loss, tp_levels)
        self.open_trades[symbol] = trade
        
        # Update strategy position
        self.strategy.update_position(symbol, side, position_size, entry_price)
        
        logger.debug(f"Position entered: {symbol} {side} {position_size} @ {entry_price}")
    
    def _check_exits(self, symbol: str, current_price: float, timestamp: datetime,
                    sl_manager: StopLossManager, tp_manager: TakeProfitManager):
        """Check if position should be exited."""
        if symbol not in self.open_trades:
            return
        
        trade = self.open_trades[symbol]
        
        # Check stop loss
        if sl_manager.check_stop_hit(symbol, current_price):
            exit_price = trade.stop_loss
            self._close_position(symbol, exit_price, timestamp, "stop_loss")
            return
        
        # Update trailing stop if applicable
        sl_manager.update_stop_loss(symbol, current_price)
        
        # Check take profit
        tp_hit = tp_manager.check_take_profit_hit(symbol, current_price)
        if tp_hit:
            level_idx, tp_price, exit_size = tp_hit
            partial_size = trade.remaining_size * exit_size
            
            if tp_manager.all_targets_filled(symbol):
                # Close entire position
                self._close_position(symbol, tp_price, timestamp, f"take_profit_final")
            else:
                # Partial close
                self._partial_close(symbol, tp_price, timestamp, partial_size, f"take_profit_{level_idx}")
    
    def _partial_close(self, symbol: str, exit_price: float, timestamp: datetime,
                      size: float, reason: str):
        """Partially close a position."""
        trade = self.open_trades[symbol]
        
        # Apply slippage
        if trade.side == 'long':
            exit_price = exit_price * (1 - self.slippage)
        else:
            exit_price = exit_price * (1 + self.slippage)
        
        # Close partial
        trade.close(timestamp, exit_price, size, reason)
        
        # Calculate proceeds
        proceeds = size * exit_price
        commission_cost = proceeds * self.commission
        
        # Update capital
        if trade.side == 'long':
            self.capital += proceeds - commission_cost + (trade.pnl / trade.size * size)
        else:
            self.capital += proceeds - commission_cost + (trade.pnl / trade.size * size)
        
        logger.debug(f"Partial close: {symbol} {size} @ {exit_price}")
    
    def _close_position(self, symbol: str, exit_price: float, timestamp: datetime, reason: str):
        """Close a position."""
        if symbol not in self.open_trades:
            return
        
        trade = self.open_trades[symbol]
        
        # Apply slippage
        if trade.side == 'long':
            exit_price = exit_price * (1 - self.slippage)
        else:
            exit_price = exit_price * (1 + self.slippage)
        
        # Close trade
        trade.close(timestamp, exit_price, trade.remaining_size, reason)
        
        # Calculate proceeds
        proceeds = trade.size * exit_price
        commission_cost = proceeds * self.commission
        
        # Update capital
        self.capital += trade.pnl - commission_cost
        
        # Move to closed trades
        self.trades.append(trade)
        del self.open_trades[symbol]
        
        # Update strategy
        self.strategy.close_position(symbol)
        
        logger.debug(f"Position closed: {symbol} @ {exit_price}, PnL: ${trade.pnl:.2f}")
    
    def _calculate_equity(self, data: Dict[str, pd.DataFrame], index: int) -> float:
        """Calculate current equity including open positions."""
        equity = self.capital
        
        for symbol, trade in self.open_trades.items():
            if symbol in data and index < len(data[symbol]):
                current_price = data[symbol].iloc[index]['close']
                
                if trade.side == 'long':
                    unrealized_pnl = (current_price - trade.entry_price) * trade.remaining_size
                else:
                    unrealized_pnl = (trade.entry_price - current_price) * trade.remaining_size
                
                equity += unrealized_pnl
        
        return equity
    
    def _calculate_results(self) -> Dict[str, Any]:
        """Calculate backtest performance metrics."""
        metrics = PerformanceMetrics(
            self.trades,
            self.initial_capital,
            self.equity_curve,
            self.timestamps
        )
        
        return metrics.calculate_all_metrics()
