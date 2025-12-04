# Crypto Futures Bot - Auto Strategy Switching System

An intelligent trading bot that automatically selects and switches between different trading strategies based on real-time market conditions.

## Features

- **Automatic Market Analysis**: Continuously analyzes volatility, trend strength, and volume
- **Smart Strategy Selection**: Matches optimal strategy to current market conditions
- **Safety Mechanisms**: 
  - Minimum strategy duration enforcement
  - Cooldown periods between switches
  - Position safety checks
  - Excessive switching protection
- **Dry-Run Mode**: Test the system without actual trading
- **Comprehensive Logging**: Detailed logs of all decisions and switches
- **Statistics Tracking**: JSON-based recording of all strategy switches

## Market Analysis

The system analyzes three key aspects of market conditions:

### Volatility Measurement
- **ATR (Average True Range)**: Absolute volatility
- **Bollinger Bandwidth**: Relative volatility
- **Price Range**: Recent high/low range
- **Classification**: LOW (0-33%), MEDIUM (33-66%), HIGH (66-100%)

### Trend Strength
- **ADX (Average Directional Index)**: Trend strength
- **EMA Alignment** (5, 20, 50): Directional confirmation
- **Linear Regression Slope**: Trend direction
- **Classification**: STRONG_UP, WEAK_UP, RANGING, WEAK_DOWN, STRONG_DOWN

### Volume Analysis
- **Volume Ratio**: Current vs average volume
- **VWAP**: Volume-weighted average price
- **Classification**: LOW, NORMAL, HIGH

## Trading Strategies

| Strategy | Best Conditions | Description |
|----------|----------------|-------------|
| **Scalping** | Medium-High volatility, Ranging/Weak trend, Normal-High volume | Short-term trades in sideways markets |
| **RSI** | Low-Medium volatility, Ranging/Weak trend, Any volume | Mean reversion strategy |
| **MACD** | Medium-High volatility, Strong trend, High volume | Trend following strategy |
| **Bollinger Bands** | High volatility, Any trend, High volume | Breakout/bounce strategy |
| **Momentum** | High volatility, Strong trend, High volume | Strong trend acceleration |
| **EMA Cross** | Medium volatility, Any trend, Normal-High volume | Trend change detection |
| **Combined** | Any conditions | Default balanced strategy |

## Installation

1. Clone the repository:
```bash
git clone https://github.com/kankanzho/crypto-futures-bot.git
cd crypto-futures-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the system:
```bash
# Edit config/config.yaml with your preferences
```

## Configuration

Edit `config/config.yaml`:

```yaml
auto_strategy_switching:
  enabled: true                    # Enable/disable auto-switching
  dry_run: true                    # Test mode (recommended for initial testing)
  check_interval: 300              # Check market every 5 minutes
  min_strategy_duration: 1800      # Keep strategy for at least 30 minutes
  switch_cooldown: 600             # Wait 10 minutes between switches
  score_threshold: 70              # Minimum score to select a strategy
  
  market_analysis:
    volatility_period: 14
    trend_period: 14
    volume_period: 20
  
  strategy_weights:
    scalping: 1.0
    rsi: 1.0
    macd: 1.0
    bollinger: 1.0
    momentum: 1.0
    ema_cross: 1.0
    combined: 0.8
```

## Usage

### Basic Usage

Run the bot with mock data:
```bash
python main.py
```

### Integration with Your Bot

```python
from core import AutoStrategyManager
from utils import load_config

# Load configuration
config = load_config('config/config.yaml')

# Create your bot instance
bot = YourTradingBot()  # Must implement required methods

# Create and start auto-strategy manager
auto_manager = AutoStrategyManager(bot, config)
auto_manager.start()

# The manager runs in a background thread
# Your bot continues normal operation
```

### Required Bot Methods

Your bot must implement these methods:

```python
class YourTradingBot:
    def get_current_strategy(self) -> str:
        """Return current strategy name"""
        pass
    
    def set_strategy(self, name: str) -> bool:
        """Set new strategy, return True if successful"""
        pass
    
    def has_open_positions(self) -> bool:
        """Return True if there are open positions"""
        pass
    
    def close_all_positions(self) -> bool:
        """Close all positions, return True if successful"""
        pass
    
    def get_market_data(self) -> pd.DataFrame:
        """Return DataFrame with OHLCV data"""
        pass
```

## Logging

The system provides detailed logging:

```
[2025-12-04 10:30:00] INFO - Market Analysis:
  Volatility: HIGH (ATR: 0.0045, BB Width: 0.038)
  Trend: STRONG_UP (ADX: 42, EMA aligned)
  Volume: HIGH (2.3x average)

[2025-12-04 10:30:01] INFO - Strategy Selection:
  1. Momentum: 95.0 points ⭐ BEST
  2. MACD: 88.0 points
  3. Bollinger: 72.0 points

[2025-12-04 10:30:02] INFO - Strategy Switch Decision:
  ✅ Different strategy recommended
  ✅ Minimum duration met
  ✅ Score 95.0 above threshold 70
  ✅ Cooldown period passed
  ✅ No open positions
  ✅ No excessive switching

[2025-12-04 10:30:03] SUCCESS - Strategy switched: scalping → momentum
```

## Statistics

All strategy switches are recorded in `data/strategy_switches.json`:

```json
{
  "switches": [
    {
      "timestamp": "2025-12-04T10:30:03Z",
      "from_strategy": "scalping",
      "to_strategy": "momentum",
      "market_condition": {
        "volatility": "HIGH",
        "trend": "STRONG_UP",
        "volume": "HIGH"
      },
      "score": 95.0,
      "forced": false,
      "dry_run": false
    }
  ]
}
```

## Safety Features

### Excessive Switching Protection
- Monitors switches in the last hour
- If 3+ switches occur, forces switch to 'combined' strategy
- Prevents rapid oscillation that increases fees

### Position Safety
- Checks for open positions before switching
- Optional: Close positions before switch (configurable)
- Never switches mid-trade unless forced

### Minimum Duration
- Each strategy runs for at least 30 minutes (configurable)
- Prevents premature strategy changes
- Allows strategies time to execute their logic

### Cooldown Period
- 10-minute wait after each switch (configurable)
- Prevents rapid back-and-forth switching
- Gives market time to stabilize

## Testing

Run tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=core --cov-report=html
```

## Development

### Project Structure
```
crypto-futures-bot/
├── core/
│   ├── __init__.py
│   ├── market_analyzer.py      # Market condition analysis
│   ├── strategy_selector.py    # Strategy selection logic
│   └── auto_strategy_manager.py # Auto-switching manager
├── config/
│   └── config.yaml              # Configuration file
├── data/
│   └── strategy_switches.json   # Switch history
├── tests/
│   ├── __init__.py
│   ├── test_market_analyzer.py
│   ├── test_strategy_selector.py
│   └── test_auto_manager.py
├── main.py                      # Entry point
├── mock_bot.py                  # Mock bot for testing
├── utils.py                     # Utility functions
└── requirements.txt             # Dependencies
```

## Roadmap

- [ ] Backtesting integration
- [ ] GUI dashboard for monitoring
- [ ] Performance analytics
- [ ] Machine learning for strategy optimization
- [ ] Support for multiple trading pairs
- [ ] Real exchange integration (Binance, etc.)

## Important Notes

⚠️ **Start with Dry-Run Mode**: Always test with `dry_run: true` before live trading

⚠️ **Minimum Testing Period**: Run in simulation for at least 1 week before live deployment

⚠️ **Fee Awareness**: Excessive switching increases trading fees - monitor switch frequency

⚠️ **Market Dependency**: Past performance doesn't guarantee future results

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: https://github.com/kankanzho/crypto-futures-bot/issues
- Email: rhrhksgh10@naver.com
