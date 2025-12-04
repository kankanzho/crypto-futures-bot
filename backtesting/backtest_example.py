"""
Backtesting Integration Example

This module demonstrates how to integrate the auto-strategy switching system
into a backtesting framework.

Note: This is a conceptual example. Actual implementation would require
a complete backtesting engine with position management, order execution, etc.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import MarketAnalyzer, StrategySelector, MarketCondition


class BacktestEngine:
    """
    Simple backtesting engine with auto-strategy switching support.
    
    This is a conceptual example showing how to integrate auto-switching
    into backtesting. A real implementation would need:
    - Order execution logic
    - Position management
    - Risk management
    - Performance metrics
    - Fee calculation
    """
    
    def __init__(self, config: dict):
        """
        Initialize backtest engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.market_analyzer = MarketAnalyzer(config)
        self.strategy_selector = StrategySelector(config)
        
        # Backtest state
        self.current_strategy = None
        self.strategy_start_idx = 0
        self.switch_history = []
        self.results = {
            'trades': [],
            'strategy_switches': [],
            'time_per_strategy': {},
            'equity_curve': []
        }
    
    def run(
        self,
        data: pd.DataFrame,
        use_auto_switching: bool = True,
        initial_strategy: str = 'combined',
        initial_capital: float = 10000
    ) -> Dict:
        """
        Run backtest on historical data.
        
        Args:
            data: Historical OHLCV DataFrame
            use_auto_switching: Enable auto strategy switching
            initial_strategy: Starting strategy
            initial_capital: Starting capital
            
        Returns:
            Dictionary with backtest results
        """
        print(f"Running backtest on {len(data)} candles...")
        print(f"Auto-switching: {use_auto_switching}")
        print(f"Initial strategy: {initial_strategy}")
        
        self.current_strategy = initial_strategy
        self.strategy_start_idx = 0
        equity = initial_capital
        
        # Get switching config
        auto_config = self.config.get('auto_strategy_switching', {})
        check_interval = auto_config.get('check_interval', 300)  # 5 minutes
        min_duration = auto_config.get('min_strategy_duration', 1800)  # 30 minutes
        
        # Convert to candles (assuming 5-minute candles)
        check_interval_candles = check_interval // 300
        min_duration_candles = min_duration // 300
        
        # Minimum data required for analysis
        min_data_period = max(
            auto_config.get('market_analysis', {}).get('volatility_period', 14),
            auto_config.get('market_analysis', {}).get('trend_period', 14),
            auto_config.get('market_analysis', {}).get('volume_period', 20)
        )
        
        # Run through historical data
        for i in range(min_data_period, len(data)):
            # Check if it's time to analyze market conditions
            if use_auto_switching and i % check_interval_candles == 0:
                # Get data window for analysis
                window_data = data.iloc[i-min_data_period:i+1]
                
                # Analyze market conditions
                try:
                    market_condition = self.market_analyzer.analyze(window_data)
                    
                    # Select best strategy
                    recommended_strategy, score = self.strategy_selector.select_best(
                        market_condition
                    )
                    
                    # Check if we should switch
                    candles_in_strategy = i - self.strategy_start_idx
                    should_switch = (
                        recommended_strategy != self.current_strategy and
                        candles_in_strategy >= min_duration_candles and
                        score >= auto_config.get('score_threshold', 70)
                    )
                    
                    if should_switch:
                        # Record switch
                        switch_record = {
                            'index': i,
                            'timestamp': data.index[i],
                            'from_strategy': self.current_strategy,
                            'to_strategy': recommended_strategy,
                            'market_condition': {
                                'volatility': market_condition.volatility,
                                'trend': market_condition.trend,
                                'volume': market_condition.volume
                            },
                            'score': score,
                            'candles_used': candles_in_strategy
                        }
                        self.switch_history.append(switch_record)
                        self.results['strategy_switches'].append(switch_record)
                        
                        # Update time per strategy
                        if self.current_strategy not in self.results['time_per_strategy']:
                            self.results['time_per_strategy'][self.current_strategy] = 0
                        self.results['time_per_strategy'][self.current_strategy] += candles_in_strategy
                        
                        # Switch strategy
                        print(f"  [{i}/{len(data)}] Switch: {self.current_strategy} → {recommended_strategy} (score: {score:.1f})")
                        self.current_strategy = recommended_strategy
                        self.strategy_start_idx = i
                
                except Exception as e:
                    print(f"  Error analyzing at index {i}: {e}")
            
            # Here you would execute the current strategy's logic
            # For now, just record equity (simplified)
            self.results['equity_curve'].append({
                'index': i,
                'timestamp': data.index[i],
                'equity': equity,
                'strategy': self.current_strategy
            })
        
        # Finalize results
        print(f"\nBacktest complete!")
        print(f"  Total strategy switches: {len(self.switch_history)}")
        print(f"  Strategies used: {list(self.results['time_per_strategy'].keys())}")
        
        return self.results
    
    def get_performance_metrics(self) -> Dict:
        """
        Calculate performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.results['equity_curve']:
            return {}
        
        equity_df = pd.DataFrame(self.results['equity_curve'])
        
        return {
            'total_switches': len(self.switch_history),
            'strategies_used': list(self.results['time_per_strategy'].keys()),
            'candles_per_strategy': self.results['time_per_strategy'],
            'switch_frequency': len(self.switch_history) / len(equity_df) if len(equity_df) > 0 else 0
        }


def example_backtest():
    """Example of running a backtest with auto-switching."""
    print("=" * 80)
    print("BACKTESTING INTEGRATION EXAMPLE")
    print("=" * 80)
    
    # Create sample configuration
    config = {
        'auto_strategy_switching': {
            'enabled': True,
            'check_interval': 300,  # 5 minutes
            'min_strategy_duration': 1800,  # 30 minutes
            'score_threshold': 70,
        },
        'market_analysis': {
            'volatility_period': 14,
            'trend_period': 14,
            'volume_period': 20
        }
    }
    
    # Generate sample historical data (simulate 3 days of 5-minute candles)
    periods = 3 * 24 * 12  # 3 days * 24 hours * 12 (5-min candles per hour)
    
    print(f"\nGenerating {periods} candles of sample data...")
    
    np.random.seed(42)
    base_price = 50000
    
    data = []
    for i in range(periods):
        # Simulate different market regimes
        if i < periods // 3:
            # First third: trending up
            drift = 0.0005
            vol = 0.001
        elif i < 2 * periods // 3:
            # Second third: ranging
            drift = 0.0
            vol = 0.0008
        else:
            # Last third: volatile
            drift = 0.0
            vol = 0.003
        
        ret = np.random.normal(drift, vol)
        if i == 0:
            price = base_price
        else:
            price = data[-1]['close'] * (1 + ret)
        
        high = price * (1 + abs(np.random.normal(0, vol)))
        low = price * (1 - abs(np.random.normal(0, vol)))
        open_price = price * np.random.uniform(0.999, 1.001)
        volume = 1000 * np.random.uniform(0.8, 1.5)
        
        data.append({
            'open': open_price,
            'high': max(high, price, open_price),
            'low': min(low, price, open_price),
            'close': price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    
    # Add timestamps (5-minute intervals)
    start_time = datetime(2025, 1, 1)
    df.index = [start_time + timedelta(minutes=5*i) for i in range(periods)]
    
    print(f"Data range: {df.index[0]} to {df.index[-1]}")
    print(f"Price range: ${df['close'].min():.2f} to ${df['close'].max():.2f}")
    
    # Run backtest with auto-switching
    print("\n" + "=" * 80)
    print("BACKTEST WITH AUTO-SWITCHING")
    print("=" * 80)
    
    engine = BacktestEngine(config)
    results = engine.run(
        data=df,
        use_auto_switching=True,
        initial_strategy='combined',
        initial_capital=10000
    )
    
    # Show results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    metrics = engine.get_performance_metrics()
    
    print(f"\nStrategy Switches: {metrics['total_switches']}")
    print(f"Strategies Used: {', '.join(metrics['strategies_used'])}")
    
    print("\nCandles per Strategy:")
    for strategy, candles in metrics['candles_per_strategy'].items():
        minutes = candles * 5
        hours = minutes / 60
        print(f"  {strategy}: {candles} candles ({hours:.1f} hours)")
    
    print(f"\nSwitch Frequency: {metrics['switch_frequency']:.4f} (switches per candle)")
    
    # Show some switch details
    if results['strategy_switches']:
        print("\nFirst 5 Strategy Switches:")
        for i, switch in enumerate(results['strategy_switches'][:5], 1):
            print(f"  {i}. {switch['timestamp'].strftime('%Y-%m-%d %H:%M')} - "
                  f"{switch['from_strategy']} → {switch['to_strategy']} "
                  f"(score: {switch['score']:.1f}, "
                  f"market: {switch['market_condition']['volatility']}/{switch['market_condition']['trend']})")


if __name__ == '__main__':
    example_backtest()
