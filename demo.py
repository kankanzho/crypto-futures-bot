"""
Demo Script - Auto Strategy Switching System

This script demonstrates how the auto-strategy switching system analyzes
market conditions and selects optimal strategies.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from core import MarketAnalyzer, StrategySelector, AutoStrategyManager
from utils import load_config
from mock_bot import MockBot


def generate_scenario_data(scenario: str, periods: int = 100) -> pd.DataFrame:
    """
    Generate market data for different scenarios.
    
    Args:
        scenario: 'trending_up', 'trending_down', 'ranging', 'volatile'
        periods: Number of candles
    
    Returns:
        DataFrame with OHLCV data
    """
    np.random.seed(42)
    base_price = 50000
    
    scenarios = {
        'trending_up': {'drift': 0.002, 'vol': 0.001},
        'trending_down': {'drift': -0.002, 'vol': 0.001},
        'ranging': {'drift': 0.0, 'vol': 0.0008},
        'volatile': {'drift': 0.0, 'vol': 0.005}
    }
    
    params = scenarios[scenario]
    
    # Generate prices
    returns = np.random.normal(params['drift'], params['vol'], periods)
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLCV
    data = []
    for i, close in enumerate(prices):
        high = close * (1 + abs(np.random.normal(0, params['vol'])))
        low = close * (1 - abs(np.random.normal(0, params['vol'])))
        open_price = close * np.random.uniform(0.999, 1.001)
        
        # Volume varies with volatility
        base_vol = 1000
        if scenario == 'volatile':
            volume = base_vol * np.random.uniform(1.5, 3.0)
        elif scenario == 'ranging':
            volume = base_vol * np.random.uniform(0.5, 1.0)
        else:
            volume = base_vol * np.random.uniform(0.8, 1.5)
        
        data.append({
            'open': open_price,
            'high': max(high, close, open_price),
            'low': min(low, close, open_price),
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    end_time = datetime.now()
    df.index = [end_time - timedelta(minutes=5*(periods-i-1)) for i in range(periods)]
    
    return df


def demo_market_analysis():
    """Demonstrate market analysis on different scenarios."""
    print("=" * 80)
    print("DEMO: Market Analysis")
    print("=" * 80)
    
    analyzer = MarketAnalyzer()
    
    scenarios = ['trending_up', 'trending_down', 'ranging', 'volatile']
    
    for scenario in scenarios:
        print(f"\n{scenario.upper().replace('_', ' ')} Market:")
        print("-" * 80)
        
        df = generate_scenario_data(scenario)
        condition = analyzer.analyze(df)
        
        print(f"  Volatility: {condition.volatility}")
        print(f"    - ATR%: {condition.metrics['atr_pct']:.4f}%")
        print(f"    - BB Width: {condition.metrics['bb_width']:.2f}%")
        print(f"    - Price Range: {condition.metrics['price_range_pct']:.2f}%")
        
        print(f"\n  Trend: {condition.trend}")
        print(f"    - ADX: {condition.metrics['adx']:.2f}")
        print(f"    - Slope: {condition.metrics['slope_pct']:.4f}%")
        print(f"    - EMA Aligned Up: {condition.metrics['ema_aligned_up']}")
        print(f"    - EMA Aligned Down: {condition.metrics['ema_aligned_down']}")
        
        print(f"\n  Volume: {condition.volume}")
        print(f"    - Volume Ratio: {condition.metrics['volume_ratio']:.2f}x average")


def demo_strategy_selection():
    """Demonstrate strategy selection for different market conditions."""
    print("\n\n")
    print("=" * 80)
    print("DEMO: Strategy Selection")
    print("=" * 80)
    
    analyzer = MarketAnalyzer()
    selector = StrategySelector()
    
    scenarios = ['trending_up', 'trending_down', 'ranging', 'volatile']
    
    for scenario in scenarios:
        print(f"\n{scenario.upper().replace('_', ' ')} Market:")
        print("-" * 80)
        
        df = generate_scenario_data(scenario)
        condition = analyzer.analyze(df)
        
        print(f"Market: Volatility={condition.volatility}, "
              f"Trend={condition.trend}, Volume={condition.volume}")
        
        # Get all strategy scores
        scores = selector.score_all_strategies(condition)
        
        print("\nTop 3 Strategies:")
        for i, strategy_score in enumerate(scores[:3], 1):
            print(f"  {i}. {strategy_score.name}: {strategy_score.score:.1f} points")
            print(f"     Reasons: {', '.join(strategy_score.reasons[:2])}")
        
        # Get best strategy
        best_strategy, score = selector.select_best(condition)
        print(f"\n⭐ Selected Strategy: {best_strategy} (score: {score:.1f})")


def demo_auto_switching():
    """Demonstrate the auto-switching manager."""
    print("\n\n")
    print("=" * 80)
    print("DEMO: Auto-Switching Manager")
    print("=" * 80)
    
    # Load config
    config = load_config('config/config.yaml')
    
    # Override some settings for demo
    config['auto_strategy_switching']['dry_run'] = True
    config['auto_strategy_switching']['min_strategy_duration'] = 0
    config['auto_strategy_switching']['switch_cooldown'] = 0
    config['auto_strategy_switching']['score_threshold'] = 60
    
    # Create bot and manager
    bot = MockBot(initial_strategy='combined')
    manager = AutoStrategyManager(bot, config)
    
    print("\nSimulating strategy switches across different market conditions...")
    
    scenarios = ['ranging', 'trending_up', 'volatile', 'trending_down']
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- Scenario {i}: {scenario.upper().replace('_', ' ')} ---")
        
        # Generate data for this scenario
        df = generate_scenario_data(scenario)
        
        # Override bot's get_market_data to return this scenario
        bot.get_market_data = lambda: df
        
        # Analyze and potentially switch
        result = manager.analyze_and_switch()
        
        print(f"Strategy switched: {result}")
        print(f"Current strategy: {manager.current_strategy}")
        
        # Show some delay
        import time
        time.sleep(0.5)
    
    # Show final statistics
    print("\n" + "=" * 80)
    print("Final Statistics:")
    stats = manager.get_statistics()
    print(f"  Total switches: {stats['total_switches']}")
    print(f"  Final strategy: {stats['current_strategy']}")
    if stats.get('time_per_strategy'):
        print("  Time per strategy:")
        for strategy, duration in stats['time_per_strategy'].items():
            print(f"    {strategy}: {duration:.1f} minutes")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "AUTO STRATEGY SWITCHING SYSTEM DEMO" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Demo 1: Market Analysis
    demo_market_analysis()
    
    # Demo 2: Strategy Selection
    demo_strategy_selection()
    
    # Demo 3: Auto-Switching
    demo_auto_switching()
    
    print("\n\n")
    print("=" * 80)
    print("Demo complete! Check out README.md for integration instructions.")
    print("=" * 80)


if __name__ == '__main__':
    main()
