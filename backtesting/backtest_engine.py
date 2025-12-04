"""
Backtesting engine for testing trading strategies.
"""

import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from strategies.base_strategy import BaseStrategy, Signal
from utils.logger import get_logger
from utils.helpers import calculate_pnl, calculate_pnl_percentage

logger = get_logger()


@dataclass
class Trade:
    """Represents a backtest trade."""
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    side: str = 'long'  # 'long' or 'short'
    quantity: float = 1.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    commission: float = 0.0
    
    def close(self, exit_time: datetime, exit_price: float, commission_rate: float = 0.075):
        """Close the trade."""
        self.exit_time = exit_time
        self.exit_price = exit_price
        
        # Calculate PnL
        gross_pnl = calculate_pnl(self.entry_price, exit_price, self.quantity, self.side)
        
        # Subtract commissions (entry + exit)
        position_value = self.entry_price * self.quantity
        self.commission = position_value * (commission_rate / 100) * 2  # Entry + Exit
        self.pnl = gross_pnl - self.commission
        self.pnl_pct = calculate_pnl_percentage(self.entry_price, exit_price, self.side)


class BacktestEngine:
    """Engine for backtesting trading strategies."""
    
    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.075,
        slippage: float = 0.05
    ):
        """
        Initialize backtest engine.
        
        Args:
            strategy: Trading strategy to test
            initial_capital: Starting capital in USDT
            commission_rate: Commission rate in percentage (0.075 = 0.075%)
            slippage: Slippage in percentage
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        # Results
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.current_capital = initial_capital
        self.current_trade: Optional[Trade] = None
        
        logger.info(f"Backtest engine initialized: {strategy.name}, Capital: ${initial_capital}")
    
    def run(self, df: pd.DataFrame) -> Dict:
        """
        Run backtest on historical data.
        
        Args:
            df: DataFrame with OHLCV data and indicators
            
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest on {len(df)} candles")
        
        self.trades = []
        self.equity_curve = [self.initial_capital]
        self.current_capital = self.initial_capital
        self.current_trade = None
        
        # Iterate through each candle
        for i in range(len(df)):
            current_row = df.iloc[i]
            current_price = current_row['close']
            current_time = current_row.get('datetime', datetime.now())
            
            # Get signal from strategy
            window_df = df.iloc[:i+1]  # Data up to current point
            signal = self.strategy.generate_signal(window_df)
            
            # Process signal
            if self.current_trade is None:
                # No open position - check for entry
                if signal.is_long() or signal.is_short():
                    if self.strategy.should_enter_trade(signal, window_df):
                        self._enter_trade(signal, current_price, current_time)
            else:
                # Have open position - check for exit
                if self._should_exit(signal, current_row):
                    self._exit_trade(current_price, current_time)
            
            # Update equity curve
            current_equity = self.current_capital
            if self.current_trade:
                unrealized_pnl = calculate_pnl(
                    self.current_trade.entry_price,
                    current_price,
                    self.current_trade.quantity,
                    self.current_trade.side
                )
                current_equity += unrealized_pnl
            
            self.equity_curve.append(current_equity)
        
        # Close any remaining open trade
        if self.current_trade:
            last_price = df.iloc[-1]['close']
            last_time = df.iloc[-1].get('datetime', datetime.now())
            self._exit_trade(last_price, last_time)
        
        logger.info(f"Backtest completed: {len(self.trades)} trades")
        
        return self._generate_results()
    
    def _enter_trade(self, signal: Signal, price: float, time: datetime) -> None:
        """Enter a trade."""
        # Apply slippage
        if signal.is_long():
            entry_price = price * (1 + self.slippage / 100)
            side = 'long'
        else:
            entry_price = price * (1 - self.slippage / 100)
            side = 'short'
        
        # Calculate position size (simple: use all capital)
        quantity = self.current_capital / entry_price
        
        self.current_trade = Trade(
            entry_time=time,
            entry_price=entry_price,
            side=side,
            quantity=quantity
        )
        
        logger.debug(f"Entered {side} trade at {entry_price}")
    
    def _exit_trade(self, price: float, time: datetime) -> None:
        """Exit current trade."""
        if not self.current_trade:
            return
        
        # Apply slippage
        if self.current_trade.side == 'long':
            exit_price = price * (1 - self.slippage / 100)
        else:
            exit_price = price * (1 + self.slippage / 100)
        
        # Close trade
        self.current_trade.close(time, exit_price, self.commission_rate)
        
        # Update capital
        self.current_capital += self.current_trade.pnl
        
        # Store trade
        self.trades.append(self.current_trade)
        
        logger.debug(f"Exited trade: PnL ${self.current_trade.pnl:.2f}")
        
        self.current_trade = None
    
    def _should_exit(self, signal: Signal, row: pd.Series) -> bool:
        """Check if should exit current trade."""
        if not self.current_trade:
            return False
        
        # Exit on opposite signal
        if self.current_trade.side == 'long' and signal.is_short():
            return True
        if self.current_trade.side == 'short' and signal.is_long():
            return True
        
        return False
    
    def _generate_results(self) -> Dict:
        """Generate backtest results summary."""
        if not self.trades:
            return {
                'total_trades': 0,
                'total_return': 0.0,
                'total_return_pct': 0.0
            }
        
        # Calculate metrics
        total_return = self.current_capital - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100
        
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        win_rate = (len(winning_trades) / len(self.trades)) * 100 if self.trades else 0
        
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        return {
            'strategy': self.strategy.name,
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss
        }
