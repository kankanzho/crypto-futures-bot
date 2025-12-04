# Usage Examples

This document provides practical examples of using the Auto Strategy Switching System.

## Table of Contents
1. [Basic Usage](#basic-usage)
2. [Custom Bot Integration](#custom-bot-integration)
3. [Configuration Examples](#configuration-examples)
4. [Monitoring and Logging](#monitoring-and-logging)
5. [Advanced Usage](#advanced-usage)

## Basic Usage

### Running with Mock Bot

The simplest way to test the system:

```bash
# Run the demo
python demo.py

# Run the main bot
python main.py
```

### Quick Start

```python
from utils import load_config
from core import AutoStrategyManager
from mock_bot import MockBot

# Load configuration
config = load_config('config/config.yaml')

# Create bot
bot = MockBot(initial_strategy='combined')

# Create and start auto-strategy manager
manager = AutoStrategyManager(bot, config)
manager.start()

# Let it run (Ctrl+C to stop)
```

## Custom Bot Integration

### Implementing Required Methods

Your trading bot must implement these methods:

```python
import pandas as pd

class MyTradingBot:
    def __init__(self):
        self.current_strategy = 'combined'
        self.positions = []
    
    def get_current_strategy(self) -> str:
        """Return the name of currently active strategy."""
        return self.current_strategy
    
    def set_strategy(self, strategy_name: str) -> bool:
        """
        Switch to a new strategy.
        
        Args:
            strategy_name: Name of the strategy to switch to
            
        Returns:
            True if switch was successful
        """
        print(f"Switching to strategy: {strategy_name}")
        self.current_strategy = strategy_name
        # Update your strategy logic here
        return True
    
    def has_open_positions(self) -> bool:
        """Check if there are any open positions."""
        return len(self.positions) > 0
    
    def close_all_positions(self) -> bool:
        """
        Close all open positions.
        
        Returns:
            True if all positions were closed successfully
        """
        for position in self.positions:
            # Close position logic here
            pass
        self.positions = []
        return True
    
    def get_market_data(self) -> pd.DataFrame:
        """
        Get current market data.
        
        Returns:
            DataFrame with columns: open, high, low, close, volume
            Index should be datetime
        """
        # Fetch from your data source
        # Example: Binance API, CSV file, database, etc.
        return self.fetch_from_exchange()
```

### Integration Example

```python
from core import AutoStrategyManager
from utils import load_config

# Your custom bot
class BinanceBot:
    # ... implement required methods ...
    pass

# Initialize
config = load_config('config/config.yaml')
bot = BinanceBot()

# Create manager
manager = AutoStrategyManager(bot, config)

# Start in separate thread
manager.start()

# Your bot continues normal operation
bot.run()

# When shutting down
manager.stop()
```

## Configuration Examples

### Conservative Trading

For stable, low-risk trading:

```yaml
auto_strategy_switching:
  enabled: true
  dry_run: false
  check_interval: 600          # Check every 10 minutes
  min_strategy_duration: 3600  # Keep strategy for 1 hour minimum
  switch_cooldown: 1800        # 30 min cooldown
  close_position_before_switch: true
  score_threshold: 80          # Higher threshold = more conservative
  
  market_analysis:
    volatility_period: 20      # Longer period = smoother
    trend_period: 20
    volume_period: 30
```

### Aggressive Trading

For active, high-frequency trading:

```yaml
auto_strategy_switching:
  enabled: true
  dry_run: false
  check_interval: 180          # Check every 3 minutes
  min_strategy_duration: 900   # Keep strategy for 15 min minimum
  switch_cooldown: 300         # 5 min cooldown
  close_position_before_switch: false
  score_threshold: 65          # Lower threshold = more switches
  
  market_analysis:
    volatility_period: 10      # Shorter period = more responsive
    trend_period: 10
    volume_period: 15
```

### Testing/Dry-Run Mode

For testing without real trades:

```yaml
auto_strategy_switching:
  enabled: true
  dry_run: true               # Only log, don't execute
  check_interval: 60          # Frequent checks for testing
  min_strategy_duration: 0    # Allow immediate switches
  switch_cooldown: 0
  score_threshold: 50
```

## Monitoring and Logging

### Reading Logs

Logs show detailed information about decisions:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Run your bot
# Logs will show market analysis and strategy decisions
```

### Analyzing Switch History

```python
import json
from pathlib import Path

# Load switch history
with open('data/strategy_switches.json') as f:
    data = json.load(f)

# Analyze switches
switches = data['switches']

print(f"Total switches: {len(switches)}")

# Count switches per strategy
from collections import Counter
to_strategies = Counter(s['to_strategy'] for s in switches)

print("\nMost selected strategies:")
for strategy, count in to_strategies.most_common():
    print(f"  {strategy}: {count} times")

# Analyze market conditions during switches
volatility_counts = Counter(
    s['market_condition']['volatility'] 
    for s in switches 
    if s.get('market_condition')
)

print("\nSwitches by volatility:")
for vol, count in volatility_counts.items():
    print(f"  {vol}: {count} switches")
```

### Real-time Statistics

```python
# Get current statistics
stats = manager.get_statistics()

print(f"Current Strategy: {stats['current_strategy']}")
print(f"Strategy Duration: {stats['strategy_duration_minutes']:.1f} minutes")
print(f"Total Switches: {stats['total_switches']}")
print(f"Switches Last Hour: {stats['switches_last_hour']}")

# Time spent per strategy
if stats.get('time_per_strategy'):
    print("\nTime per strategy:")
    for strategy, minutes in stats['time_per_strategy'].items():
        print(f"  {strategy}: {minutes:.1f} minutes")
```

## Advanced Usage

### Manual Override

Temporarily disable auto-switching:

```python
# Stop auto-switching
manager.stop()

# Manually set strategy
bot.set_strategy('momentum')

# Resume auto-switching later
manager.start()
```

### Custom Strategy Weights

Prefer certain strategies:

```python
config = {
    'auto_strategy_switching': {
        'strategy_weights': {
            'momentum': 1.5,   # 50% more likely to select
            'scalping': 0.8,   # 20% less likely to select
            'macd': 1.2,
            # ... others default to 1.0
        }
    }
}

manager = AutoStrategyManager(bot, config)
```

### Conditional Switching

Only switch in certain conditions:

```python
class ConditionalManager(AutoStrategyManager):
    def _should_switch(self, recommended_strategy, score):
        # Call parent logic
        should_switch = super()._should_switch(recommended_strategy, score)
        
        # Add custom conditions
        if should_switch:
            # Only switch during market hours
            from datetime import datetime
            now = datetime.now()
            if now.hour < 9 or now.hour > 16:
                return False
            
            # Only switch if score is very high
            if score < 85:
                return False
        
        return should_switch
```

### Event Callbacks

Get notified of switches:

```python
class CallbackManager(AutoStrategyManager):
    def __init__(self, bot, config, on_switch=None):
        super().__init__(bot, config)
        self.on_switch = on_switch
    
    def _execute_switch(self, new_strategy, market_condition, score, force=False):
        # Execute switch
        result = super()._execute_switch(
            new_strategy, market_condition, score, force
        )
        
        # Call callback
        if result and self.on_switch:
            self.on_switch(
                old_strategy=self.current_strategy,
                new_strategy=new_strategy,
                condition=market_condition,
                score=score
            )
        
        return result

# Usage
def on_strategy_switch(old_strategy, new_strategy, condition, score):
    print(f"🔄 Strategy changed: {old_strategy} → {new_strategy}")
    # Send notification, update UI, etc.

manager = CallbackManager(bot, config, on_switch=on_strategy_switch)
```

### Backtesting Integration

Test the system on historical data:

```python
from backtesting import BacktestEngine

# Load historical data
historical_data = pd.read_csv('historical_data.csv', index_col='timestamp', parse_dates=True)

# Configure
config = load_config('config/config.yaml')

# Run backtest
engine = BacktestEngine(config)
results = engine.run(
    data=historical_data,
    use_auto_switching=True,
    initial_strategy='combined',
    initial_capital=10000
)

# Analyze results
print(f"Strategy switches: {len(results['strategy_switches'])}")
print(f"Time per strategy: {results['time_per_strategy']}")
```

## Tips and Best Practices

1. **Start with dry-run mode** - Always test with `dry_run: true` first
2. **Monitor for a week** - Observe strategy selections before going live
3. **Adjust thresholds gradually** - Don't make large changes to score_threshold
4. **Watch switch frequency** - Too many switches increase fees
5. **Review logs regularly** - Check that switches make sense
6. **Backtest first** - Test on historical data before live trading
7. **Use conservative settings** - Better to miss opportunities than take bad trades
8. **Monitor performance** - Track which strategies perform best
9. **Keep records** - Save all switch history for analysis
10. **Have a kill switch** - Be ready to stop auto-switching if needed

## Troubleshooting

### System keeps switching to 'combined'

- Score threshold may be too high
- Market conditions may not match any strategy well
- Reduce `score_threshold` or adjust strategy rules

### Too many switches

- Increase `min_strategy_duration`
- Increase `switch_cooldown`
- Increase `score_threshold`

### Not switching when it should

- Check if positions are open (blocks switching)
- Verify `min_strategy_duration` has passed
- Check if cooldown period is active
- Review logs for specific rejection reasons

### Market analysis errors

- Ensure sufficient historical data (at least 50 candles)
- Verify DataFrame has required columns: open, high, low, close, volume
- Check for NaN values in data
