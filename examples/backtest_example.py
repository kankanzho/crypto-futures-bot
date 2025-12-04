"""
Example backtest script.
Demonstrates how to backtest a strategy on historical data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategies import RSIStrategy, MACDStrategy
from src.backtesting import BacktestEngine, StrategyOptimizer
from src.backtesting.performance_metrics import PerformanceMetrics


def generate_sample_data(symbol: str, days: int = 30) -> pd.DataFrame:
    """
    Generate sample OHLCV data for testing.
    
    Args:
        symbol: Trading pair symbol
        days: Number of days of data
        
    Returns:
        DataFrame with OHLCV data
    """
    # Generate timestamps
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    timestamps = pd.date_range(start=start_date, end=end_date, freq='1min')
    
    # Generate price data with trend and noise
    np.random.seed(42)
    
    # Base price
    base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 100
    
    # Add trend and random walk
    trend = np.linspace(0, base_price * 0.1, len(timestamps))
    random_walk = np.cumsum(np.random.randn(len(timestamps)) * base_price * 0.002)
    close_prices = base_price + trend + random_walk
    
    # Generate OHLCV
    df = pd.DataFrame({
        'open': close_prices + np.random.randn(len(timestamps)) * base_price * 0.001,
        'high': close_prices + np.abs(np.random.randn(len(timestamps)) * base_price * 0.003),
        'low': close_prices - np.abs(np.random.randn(len(timestamps)) * base_price * 0.003),
        'close': close_prices,
        'volume': np.random.randint(100, 1000, len(timestamps))
    }, index=timestamps)
    
    return df


def run_simple_backtest():
    """Run a simple backtest with RSI strategy."""
    print("=" * 60)
    print("SIMPLE BACKTEST EXAMPLE")
    print("=" * 60)
    
    # Generate sample data
    print("\nGenerating sample data...")
    data = {
        'BTCUSDT': generate_sample_data('BTCUSDT', days=30)
    }
    
    print(f"Data generated: {len(data['BTCUSDT'])} candles")
    
    # Create strategy
    print("\nInitializing RSI strategy...")
    strategy_params = {
        'period': 14,
        'oversold': 30,
        'overbought': 70
    }
    strategy = RSIStrategy(strategy_params)
    
    # Configure risk management
    stop_loss_config = {
        'type': 'percentage',
        'value': 0.02  # 2% stop loss
    }
    
    take_profit_config = {
        'type': 'risk_reward',
        'ratio': 2.0  # 2:1 risk/reward
    }
    
    position_size_config = {
        'method': 'fixed_risk',
        'risk_per_trade': 0.02,  # Risk 2% per trade
        'max_positions': 4
    }
    
    # Run backtest
    print("\nRunning backtest...")
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=10000,
        commission=0.0006,  # 0.06% commission
        slippage=0.0005,    # 0.05% slippage
        leverage=10
    )
    
    results = engine.run(
        data=data,
        stop_loss_config=stop_loss_config,
        take_profit_config=take_profit_config,
        position_size_config=position_size_config
    )
    
    # Print results
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    
    print(f"\nReturn Metrics:")
    print(f"  Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"  Final Equity: ${results['final_equity']:,.2f}")
    print(f"  Total Return: ${results['total_return']:,.2f} ({results['total_return_pct']:.2f}%)")
    print(f"  Annualized Return: {results['annualized_return']:.2f}%")
    
    print(f"\nRisk Metrics:")
    print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"  Sortino Ratio: {results['sortino_ratio']:.2f}")
    print(f"  Max Drawdown: ${results['max_drawdown']:,.2f} ({results['max_drawdown_pct']:.2f}%)")
    print(f"  Volatility (Annual): {results['annualized_volatility']:.2f}%")
    
    print(f"\nTrade Statistics:")
    print(f"  Total Trades: {results['total_trades']}")
    print(f"  Winning Trades: {results['winning_trades']}")
    print(f"  Losing Trades: {results['losing_trades']}")
    print(f"  Win Rate: {results['win_rate']:.2f}%")
    print(f"  Profit Factor: {results['profit_factor']:.2f}")
    print(f"  Average Win: ${results['avg_win']:,.2f} ({results['avg_win_pct']:.2f}%)")
    print(f"  Average Loss: ${results['avg_loss']:,.2f} ({results['avg_loss_pct']:.2f}%)")
    
    print(f"\nAdditional Metrics:")
    print(f"  Expectancy: ${results['expectancy']:,.2f}")
    print(f"  Recovery Factor: {results['recovery_factor']:.2f}")
    print(f"  Calmar Ratio: {results['calmar_ratio']:.2f}")
    
    print("\n" + "=" * 60)
    
    return results


def main():
    """Main function."""
    print("\nCrypto Futures Bot - Backtest Example")
    print("=" * 60)
    
    # Run simple backtest
    backtest_results = run_simple_backtest()
    
    print("\n✅ Example completed!")
    print("\nNext steps:")
    print("  1. Review the results above")
    print("  2. Try different strategies (MACD, Bollinger, EMA)")
    print("  3. Adjust parameters to improve performance")
    print("  4. Test on real historical data from Bybit")
    print("  5. Run on testnet before going live")
    
    print("\n⚠️  Remember: Past performance does not guarantee future results!")


if __name__ == "__main__":
    main()
