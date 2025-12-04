"""
Performance metrics calculator for backtesting.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger


class PerformanceMetrics:
    """Calculates various performance metrics for backtest results."""
    
    def __init__(self, trades: List, initial_capital: float,
                 equity_curve: List[float], timestamps: List[datetime]):
        """
        Initialize performance metrics calculator.
        
        Args:
            trades: List of completed trades
            initial_capital: Initial capital
            equity_curve: List of equity values over time
            timestamps: List of timestamps corresponding to equity curve
        """
        self.trades = trades
        self.initial_capital = initial_capital
        self.equity_curve = equity_curve
        self.timestamps = timestamps
        
        # Calculate returns
        self.returns = self._calculate_returns()
    
    def _calculate_returns(self) -> np.ndarray:
        """Calculate period returns from equity curve."""
        if len(self.equity_curve) < 2:
            return np.array([])
        
        equity_array = np.array(self.equity_curve)
        returns = np.diff(equity_array) / equity_array[:-1]
        
        return returns
    
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """
        Calculate all performance metrics.
        
        Returns:
            Dictionary with all metrics
        """
        metrics = {
            # Return metrics
            'total_return': self.total_return(),
            'total_return_pct': self.total_return_percent(),
            'annualized_return': self.annualized_return(),
            'cagr': self.cagr(),
            
            # Risk metrics
            'sharpe_ratio': self.sharpe_ratio(),
            'sortino_ratio': self.sortino_ratio(),
            'max_drawdown': self.max_drawdown(),
            'max_drawdown_pct': self.max_drawdown_percent(),
            'volatility': self.volatility(),
            'annualized_volatility': self.annualized_volatility(),
            
            # Trade statistics
            'total_trades': self.total_trades(),
            'winning_trades': self.winning_trades(),
            'losing_trades': self.losing_trades(),
            'win_rate': self.win_rate(),
            'avg_win': self.average_win(),
            'avg_loss': self.average_loss(),
            'avg_win_pct': self.average_win_percent(),
            'avg_loss_pct': self.average_loss_percent(),
            'profit_factor': self.profit_factor(),
            'largest_win': self.largest_win(),
            'largest_loss': self.largest_loss(),
            
            # Additional metrics
            'avg_trade_duration': self.average_trade_duration(),
            'expectancy': self.expectancy(),
            'recovery_factor': self.recovery_factor(),
            'calmar_ratio': self.calmar_ratio(),
            
            # Final values
            'final_equity': self.final_equity(),
            'initial_capital': self.initial_capital,
        }
        
        return metrics
    
    # Return metrics
    
    def total_return(self) -> float:
        """Calculate total return in dollars."""
        if not self.equity_curve:
            return 0
        return self.equity_curve[-1] - self.initial_capital
    
    def total_return_percent(self) -> float:
        """Calculate total return as percentage."""
        if self.initial_capital == 0:
            return 0
        return (self.total_return() / self.initial_capital) * 100
    
    def annualized_return(self) -> float:
        """Calculate annualized return."""
        if not self.timestamps or len(self.timestamps) < 2:
            return 0
        
        days = (self.timestamps[-1] - self.timestamps[0]).days
        if days == 0:
            return 0
        
        years = days / 365.25
        total_return_ratio = self.equity_curve[-1] / self.initial_capital
        
        return (total_return_ratio ** (1 / years) - 1) * 100
    
    def cagr(self) -> float:
        """Calculate Compound Annual Growth Rate."""
        return self.annualized_return()
    
    # Risk metrics
    
    def sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            risk_free_rate: Annual risk-free rate (default: 2%)
            
        Returns:
            Sharpe ratio
        """
        if len(self.returns) == 0:
            return 0
        
        # Annualize returns
        daily_rf_rate = (1 + risk_free_rate) ** (1/365) - 1
        excess_returns = self.returns - daily_rf_rate
        
        if np.std(excess_returns) == 0:
            return 0
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns)
        
        # Annualize (assuming daily returns)
        sharpe_annual = sharpe * np.sqrt(365)
        
        return sharpe_annual
    
    def sortino_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sortino ratio (uses downside deviation).
        
        Args:
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Sortino ratio
        """
        if len(self.returns) == 0:
            return 0
        
        daily_rf_rate = (1 + risk_free_rate) ** (1/365) - 1
        excess_returns = self.returns - daily_rf_rate
        
        # Calculate downside deviation
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return 0
        
        downside_dev = np.std(downside_returns)
        if downside_dev == 0:
            return 0
        
        sortino = np.mean(excess_returns) / downside_dev
        sortino_annual = sortino * np.sqrt(365)
        
        return sortino_annual
    
    def max_drawdown(self) -> float:
        """Calculate maximum drawdown in dollars."""
        if not self.equity_curve:
            return 0
        
        equity = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown = running_max - equity
        
        return np.max(drawdown)
    
    def max_drawdown_percent(self) -> float:
        """Calculate maximum drawdown as percentage."""
        if not self.equity_curve:
            return 0
        
        equity = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown_pct = (running_max - equity) / running_max * 100
        
        return np.max(drawdown_pct)
    
    def volatility(self) -> float:
        """Calculate return volatility (standard deviation)."""
        if len(self.returns) == 0:
            return 0
        return np.std(self.returns)
    
    def annualized_volatility(self) -> float:
        """Calculate annualized volatility."""
        return self.volatility() * np.sqrt(365) * 100
    
    # Trade statistics
    
    def total_trades(self) -> int:
        """Total number of trades."""
        return len(self.trades)
    
    def winning_trades(self) -> int:
        """Number of winning trades."""
        return sum(1 for trade in self.trades if trade.pnl > 0)
    
    def losing_trades(self) -> int:
        """Number of losing trades."""
        return sum(1 for trade in self.trades if trade.pnl < 0)
    
    def win_rate(self) -> float:
        """Win rate as percentage."""
        total = self.total_trades()
        if total == 0:
            return 0
        return (self.winning_trades() / total) * 100
    
    def average_win(self) -> float:
        """Average winning trade amount."""
        wins = [trade.pnl for trade in self.trades if trade.pnl > 0]
        return np.mean(wins) if wins else 0
    
    def average_loss(self) -> float:
        """Average losing trade amount."""
        losses = [trade.pnl for trade in self.trades if trade.pnl < 0]
        return np.mean(losses) if losses else 0
    
    def average_win_percent(self) -> float:
        """Average winning trade percentage."""
        wins = [trade.pnl_percent for trade in self.trades if trade.pnl > 0]
        return np.mean(wins) if wins else 0
    
    def average_loss_percent(self) -> float:
        """Average losing trade percentage."""
        losses = [trade.pnl_percent for trade in self.trades if trade.pnl < 0]
        return np.mean(losses) if losses else 0
    
    def profit_factor(self) -> float:
        """Profit factor (gross profit / gross loss)."""
        gross_profit = sum(trade.pnl for trade in self.trades if trade.pnl > 0)
        gross_loss = abs(sum(trade.pnl for trade in self.trades if trade.pnl < 0))
        
        if gross_loss == 0:
            return 0 if gross_profit == 0 else float('inf')
        
        return gross_profit / gross_loss
    
    def largest_win(self) -> float:
        """Largest winning trade."""
        wins = [trade.pnl for trade in self.trades if trade.pnl > 0]
        return max(wins) if wins else 0
    
    def largest_loss(self) -> float:
        """Largest losing trade."""
        losses = [trade.pnl for trade in self.trades if trade.pnl < 0]
        return min(losses) if losses else 0
    
    # Additional metrics
    
    def average_trade_duration(self) -> float:
        """Average trade duration in hours."""
        if not self.trades:
            return 0
        
        durations = []
        for trade in self.trades:
            if trade.exit_time and trade.entry_time:
                duration = (trade.exit_time - trade.entry_time).total_seconds() / 3600
                durations.append(duration)
        
        return np.mean(durations) if durations else 0
    
    def expectancy(self) -> float:
        """
        Calculate expectancy per trade.
        
        Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)
        """
        win_rate = self.win_rate() / 100
        loss_rate = 1 - win_rate
        
        avg_win = self.average_win()
        avg_loss = abs(self.average_loss())
        
        return (win_rate * avg_win) - (loss_rate * avg_loss)
    
    def recovery_factor(self) -> float:
        """
        Recovery factor (Net Profit / Max Drawdown).
        
        Measures how many times the max drawdown is recovered.
        """
        max_dd = self.max_drawdown()
        if max_dd == 0:
            return 0
        
        return self.total_return() / max_dd
    
    def calmar_ratio(self) -> float:
        """
        Calmar ratio (Annualized Return / Max Drawdown %).
        
        Measures return relative to maximum drawdown.
        """
        max_dd_pct = self.max_drawdown_percent()
        if max_dd_pct == 0:
            return 0
        
        return self.annualized_return() / max_dd_pct
    
    def final_equity(self) -> float:
        """Final equity value."""
        return self.equity_curve[-1] if self.equity_curve else self.initial_capital
    
    def print_summary(self):
        """Print performance summary."""
        metrics = self.calculate_all_metrics()
        
        print("\n" + "="*60)
        print("BACKTEST PERFORMANCE SUMMARY")
        print("="*60)
        
        print("\nReturn Metrics:")
        print(f"  Total Return: ${metrics['total_return']:.2f} ({metrics['total_return_pct']:.2f}%)")
        print(f"  Annualized Return: {metrics['annualized_return']:.2f}%")
        print(f"  Final Equity: ${metrics['final_equity']:.2f}")
        
        print("\nRisk Metrics:")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Sortino Ratio: {metrics['sortino_ratio']:.2f}")
        print(f"  Max Drawdown: ${metrics['max_drawdown']:.2f} ({metrics['max_drawdown_pct']:.2f}%)")
        print(f"  Volatility (Annual): {metrics['annualized_volatility']:.2f}%")
        
        print("\nTrade Statistics:")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Win Rate: {metrics['win_rate']:.2f}%")
        print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"  Average Win: ${metrics['avg_win']:.2f} ({metrics['avg_win_pct']:.2f}%)")
        print(f"  Average Loss: ${metrics['avg_loss']:.2f} ({metrics['avg_loss_pct']:.2f}%)")
        print(f"  Largest Win: ${metrics['largest_win']:.2f}")
        print(f"  Largest Loss: ${metrics['largest_loss']:.2f}")
        
        print("\nAdditional Metrics:")
        print(f"  Expectancy: ${metrics['expectancy']:.2f}")
        print(f"  Recovery Factor: {metrics['recovery_factor']:.2f}")
        print(f"  Calmar Ratio: {metrics['calmar_ratio']:.2f}")
        print(f"  Avg Trade Duration: {metrics['avg_trade_duration']:.2f} hours")
        
        print("="*60 + "\n")
