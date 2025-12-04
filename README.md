# Crypto Futures Trading Bot

A professional cryptocurrency futures automated trading bot system for Bybit exchange, built with Python.

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ⚠️ Risk Warning

**IMPORTANT:** Cryptocurrency futures trading involves substantial risk of loss. This bot is provided for educational purposes. Always:
- Test thoroughly on testnet before using real funds
- Start with small amounts
- Never invest more than you can afford to lose
- Understand that past performance does not guarantee future results

## 🎯 Features

### Trading Strategies
- **RSI (Relative Strength Index)**: Momentum-based strategy using overbought/oversold levels
- **MACD (Moving Average Convergence Divergence)**: Trend-following momentum strategy
- **Bollinger Bands**: Volatility-based mean reversion strategy
- **EMA Crossover**: Trend detection using exponential moving averages
- **Hot-swappable strategies**: Change strategies without restarting the bot

### Risk Management
- **Stop Loss**: Percentage-based, ATR-based, and trailing stop losses
- **Take Profit**: Multi-level take profit, risk/reward ratio-based, and dynamic targets
- **Position Sizing**: Kelly Criterion and fixed risk percentage methods
- **Risk Limits**: Daily and weekly maximum loss limits with emergency stop

### Backtesting System
- **Multi-strategy backtesting**: Test all strategies independently
- **Performance Metrics**: 
  - Returns: Total return, annualized return, CAGR
  - Risk: Sharpe ratio, Sortino ratio, Maximum Drawdown
  - Trade stats: Win rate, profit factor, expectancy
- **Parameter Optimization**: Grid search and walk-forward optimization
- **Visual Analysis**: Equity curves, drawdown charts, trade distribution

### Exchange Integration
- **Bybit API v5**: Full integration with latest API
- **Real-time Data**: WebSocket support for live market data
- **Rate Limiting**: Automatic request throttling (120 req/s limit)
- **Retry Logic**: Exponential backoff for failed requests
- **Multi-coin Support**: Trade 3-4 coins simultaneously (BTC, ETH, SOL, BNB)

### Advanced Features
- **Multi-timeframe Analysis**: Confirm trends across different timeframes
- **Short Timeframe Optimization**: Optimized for 1-minute and 3-minute scalping
- **Leverage Management**: Automatic leverage configuration per coin
- **Comprehensive Logging**: Detailed logs with rotation and compression
- **Performance Tracking**: Real-time equity curve and trade history

## 📋 Requirements

- Python 3.10 or higher
- Bybit account (testnet or mainnet)
- API key and secret from Bybit

## 🚀 Installation

1. **Clone the repository**
```bash
git clone https://github.com/kankanzho/crypto-futures-bot.git
cd crypto-futures-bot
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure API credentials**
```bash
cp config/.env.example .env
```

Edit `.env` and add your Bybit API credentials:
```env
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET=true  # Set to false for mainnet
INITIAL_CAPITAL=10000
MAX_POSITION_SIZE=1000
```

## ⚙️ Configuration

### Main Configuration (`config/config.yaml`)

```yaml
trading:
  mode: "testnet"  # or "live"
  
  coins:
    - symbol: "BTCUSDT"
      allocation: 0.4  # 40% of capital
      leverage: 10
      enabled: true
    - symbol: "ETHUSDT"
      allocation: 0.3
      leverage: 10
      enabled: true
  
  position_sizing:
    method: "fixed_risk"  # or "kelly_criterion"
    risk_per_trade: 0.02  # 2% per trade
    max_positions: 4
  
  risk_management:
    max_daily_loss: 0.05      # 5% max daily loss
    max_weekly_loss: 0.15     # 15% max weekly loss
    emergency_stop_loss: 0.20  # 20% emergency stop
```

### Strategy Configuration (`config/strategies.yaml`)

```yaml
rsi:
  enabled: true
  parameters:
    period: 14
    oversold: 30
    overbought: 70
  stop_loss:
    type: "percentage"
    value: 0.02  # 2%
  take_profit:
    type: "risk_reward"
    ratio: 2.0  # 2:1 R/R
```

## 📊 Usage

### Running the Bot

```bash
python src/main.py
```

### Backtesting a Strategy

```python
from src.backtesting import BacktestEngine
from src.strategies import RSIStrategy
import pandas as pd

# Load historical data
data = {
    'BTCUSDT': pd.read_csv('data/BTCUSDT_1m.csv')
}

# Create strategy
strategy = RSIStrategy({'period': 14, 'oversold': 30, 'overbought': 70})

# Run backtest
engine = BacktestEngine(strategy, initial_capital=10000)
results = engine.run(
    data,
    stop_loss_config={'type': 'percentage', 'value': 0.02},
    take_profit_config={'type': 'risk_reward', 'ratio': 2.0},
    position_size_config={'method': 'fixed_risk', 'risk_per_trade': 0.02}
)

# Print results
print(f"Total Return: {results['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Win Rate: {results['win_rate']:.2f}%")
```

### Optimizing Strategy Parameters

```python
from src.backtesting import StrategyOptimizer
from src.strategies import RSIStrategy

optimizer = StrategyOptimizer(RSIStrategy, initial_capital=10000)

results = optimizer.optimize(
    data=data,
    param_ranges={
        'period': [10, 14, 18, 21],
        'oversold': [25, 30, 35],
        'overbought': [65, 70, 75]
    },
    stop_loss_config={'type': 'percentage', 'value': 0.02},
    take_profit_config={'type': 'risk_reward', 'ratio': 2.0},
    position_size_config={'method': 'fixed_risk', 'risk_per_trade': 0.02},
    metric='sharpe_ratio'
)

print(f"Best parameters: {results['best_parameters']}")
print(f"Best Sharpe: {results['best_score']:.2f}")
```

## 📁 Project Structure

```
crypto-futures-bot/
├── config/
│   ├── config.yaml          # Bot configuration
│   ├── strategies.yaml      # Strategy parameters
│   └── .env.example         # API key template
├── src/
│   ├── strategies/          # Trading strategies
│   │   ├── base_strategy.py
│   │   ├── rsi_strategy.py
│   │   ├── macd_strategy.py
│   │   ├── bollinger_strategy.py
│   │   └── ema_cross_strategy.py
│   ├── risk_management/     # Risk management
│   │   ├── stop_loss.py
│   │   ├── take_profit.py
│   │   └── position_sizer.py
│   ├── exchange/            # Exchange integration
│   │   ├── bybit_client.py
│   │   └── websocket_handler.py
│   ├── backtesting/         # Backtesting engine
│   │   ├── backtest_engine.py
│   │   ├── performance_metrics.py
│   │   └── optimizer.py
│   ├── utils/               # Utilities
│   │   ├── logger.py
│   │   ├── indicators.py
│   │   └── helpers.py
│   └── main.py              # Main bot execution
├── tests/                   # Test files
├── data/                    # Historical data
├── logs/                    # Log files
├── results/                 # Backtest results
├── requirements.txt
└── README.md
```

## 🔧 Strategy Development

Create a custom strategy by inheriting from `BaseStrategy`:

```python
from src.strategies.base_strategy import BaseStrategy, SignalType
import pandas as pd

class CustomStrategy(BaseStrategy):
    def __init__(self, parameters):
        super().__init__("Custom Strategy", parameters)
        self.threshold = parameters.get('threshold', 0.5)
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        # Add your indicators
        df = data.copy()
        df['custom_indicator'] = ...  # Your calculation
        return df
    
    def generate_signal(self, symbol: str, data: pd.DataFrame) -> SignalType:
        df = self.calculate_indicators(data)
        
        # Your signal logic
        if df['custom_indicator'].iloc[-1] > self.threshold:
            return SignalType.BUY
        elif df['custom_indicator'].iloc[-1] < -self.threshold:
            return SignalType.SELL
        
        return SignalType.HOLD
```

## 📈 Performance Metrics

The backtesting engine calculates comprehensive metrics:

### Return Metrics
- Total Return ($ and %)
- Annualized Return
- CAGR (Compound Annual Growth Rate)

### Risk Metrics
- Sharpe Ratio (risk-adjusted return)
- Sortino Ratio (downside deviation)
- Maximum Drawdown ($ and %)
- Volatility (annualized)
- Calmar Ratio (return/drawdown)

### Trade Statistics
- Total Trades
- Win Rate
- Profit Factor
- Average Win/Loss
- Largest Win/Loss
- Expectancy
- Average Trade Duration

## 🛡️ Risk Management

### Position Sizing Methods

**Fixed Risk**: Risk a fixed percentage per trade
```yaml
position_sizing:
  method: "fixed_risk"
  risk_per_trade: 0.02  # 2%
```

**Kelly Criterion**: Optimal position sizing based on edge
```yaml
position_sizing:
  method: "kelly_criterion"
  kelly_fraction: 0.25  # Use 25% of Kelly
```

### Stop Loss Types

**Percentage-based**:
```yaml
stop_loss:
  type: "percentage"
  value: 0.02  # 2%
```

**ATR-based** (adapts to volatility):
```yaml
stop_loss:
  type: "atr"
  multiplier: 2.0
  atr_period: 14
```

**Trailing Stop**:
```yaml
stop_loss:
  type: "trailing"
  initial_stop: 0.015      # 1.5% initial
  trailing_percent: 0.01   # 1% trail
  activation_percent: 0.01 # Activate after 1% profit
```

## 🔐 Security Best Practices

1. **Never commit API keys**: Keep `.env` file in `.gitignore`
2. **Use testnet first**: Always test thoroughly before going live
3. **Enable IP whitelist**: Configure IP restrictions in Bybit
4. **Limit API permissions**: Only enable necessary permissions
5. **Monitor logs**: Regularly check logs for suspicious activity
6. **Start small**: Begin with minimal capital to test

## 🧪 Testing

Run tests with pytest:
```bash
pytest tests/ -v
```

## 📝 Logging

Logs are stored in the `logs/` directory:
- `bot_YYYY-MM-DD.log`: Daily bot activity
- `error_YYYY-MM-DD.log`: Error logs only
- Automatic rotation and compression
- 30-day retention by default

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚡ Performance Targets

The bot aims to achieve:
- ✅ Win rate: 55%+
- ✅ Sharpe ratio: 1.5+
- ✅ Profit factor: 2.0+
- ✅ Risk/Reward: 2:1 minimum

## 🐛 Troubleshooting

### Common Issues

**API Connection Errors**
```
Solution: Check API credentials and network connectivity
```

**Insufficient Data Error**
```
Solution: Ensure enough historical data for indicator calculation (min 100 bars)
```

**Rate Limit Exceeded**
```
Solution: Reduce request frequency in config or increase delay
```

## 📚 Resources

- [Bybit API Documentation](https://bybit-exchange.github.io/docs/v5/intro)
- [Technical Analysis Library](https://technical-analysis-library-in-python.readthedocs.io/)
- [Backtrader Documentation](https://www.backtrader.com/docu/)

## 💬 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review documentation thoroughly

## 📊 Roadmap

- [ ] Add more trading strategies
- [ ] Implement ML-based strategies
- [ ] Add Telegram notifications
- [ ] Create web-based dashboard
- [ ] Support for more exchanges
- [ ] Portfolio optimization
- [ ] Advanced order types

---

**Disclaimer**: This software is for educational purposes only. Use at your own risk. The authors are not responsible for any financial losses incurred while using this bot.
