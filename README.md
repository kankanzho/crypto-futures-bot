# 🚀 Bybit Cryptocurrency Futures Trading Bot

A comprehensive automated trading bot for Bybit cryptocurrency futures markets, optimized for scalping strategies with real-time monitoring GUI and backtesting capabilities.

## ✨ Features

### 🎯 Multiple Trading Strategies
- **Scalping Strategy**: High-frequency trading on 1-minute timeframes
- **RSI Strategy**: Reversal trading based on overbought/oversold conditions
- **MACD Strategy**: Trend-following using MACD crossovers
- **Bollinger Bands Strategy**: Volatility breakout trading
- **Momentum Strategy**: Rate of change-based momentum trading
- **EMA Cross Strategy**: Moving average crossover signals
- **Combined Strategy**: Multi-strategy signal combination

### 🛡️ Advanced Risk Management
- Configurable stop-loss and take-profit levels
- Trailing stop functionality
- ATR-based dynamic stops
- Position sizing based on account risk
- Maximum daily loss limits
- Partial profit-taking
- Risk-reward ratio enforcement

### 📊 Backtesting System
- Historical data analysis
- Multiple timeframe support
- Performance metrics calculation (Sharpe ratio, Max Drawdown, Profit Factor)
- Strategy optimization
- Visual equity curves and trade analysis

### 🖥️ Real-time GUI Dashboard
- Live price charts with technical indicators
- Position and trade history monitoring
- Account balance and P&L tracking
- Strategy control panel
- Real-time logging
- Emergency position closure

### 🔌 Bybit API Integration
- REST API for orders and account management
- WebSocket for real-time market data
- Rate limit management
- Automatic reconnection handling

## 📋 Requirements

- Python 3.9 or higher
- Bybit account (Testnet or Mainnet)
- Bybit API credentials

## 🔧 Installation

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

Note: TA-Lib requires additional installation steps. See [TA-Lib Installation Guide](https://github.com/mrjbq7/ta-lib#installation)

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your Bybit API credentials
```

5. **Configure trading parameters**
Edit configuration files in the `config/` directory:
- `config.yaml` - Main trading configuration
- `strategy_params.yaml` - Strategy-specific parameters
- `coins.yaml` - Trading pairs configuration

## 🚀 Usage

### Running the Bot

```bash
python main.py
```

This will launch the GUI dashboard where you can:
- Start/stop trading
- Monitor positions and performance
- Switch between strategies
- Run backtests
- View real-time charts

### Configuration

#### Main Configuration (`config/config.yaml`)

```yaml
trading:
  mode: testnet  # testnet or mainnet
  leverage: 10
  max_positions: 4
  position_size_pct: 25

risk_management:
  stop_loss_pct: 2.0
  take_profit_pct: 3.0
  trailing_stop: true
  max_daily_loss_pct: 5.0
```

#### Strategy Selection

Set the active strategy in `config/config.yaml`:
```yaml
strategies:
  active_strategy: scalping  # Options: scalping, rsi, macd, bollinger, momentum, ema_cross, combined
```

#### Coin Selection

Enable/disable trading pairs in `config/coins.yaml`:
```yaml
coins:
  - symbol: BTCUSDT
    enabled: true
    allocation_pct: 25
```

## 📊 Trading Strategies

### Scalping Strategy
- **Timeframe**: 1 minute
- **Indicators**: EMA(5), EMA(13), RSI(14), Volume
- **Best for**: High volatility, liquid markets
- **Average hold time**: 5-30 minutes

### RSI Strategy
- **Timeframe**: 3 minutes
- **Indicators**: RSI(14)
- **Signals**: Oversold (<30) for long, Overbought (>70) for short
- **Best for**: Range-bound markets

### MACD Strategy
- **Timeframe**: 5 minutes
- **Indicators**: MACD(12,26,9)
- **Signals**: MACD line crosses signal line
- **Best for**: Trending markets

### Bollinger Bands Strategy
- **Timeframe**: 3 minutes
- **Indicators**: BB(20, 2)
- **Signals**: Price touches bands and reverses
- **Best for**: Volatile markets with mean reversion

### Combined Strategy
- Uses multiple strategies simultaneously
- Requires minimum 2 confirmations to enter trades
- Weighted voting system for signal strength

## 🔍 Backtesting

Run backtests through the GUI or programmatically:

```python
from backtesting.backtest_engine import BacktestEngine

engine = BacktestEngine(
    strategy='scalping',
    symbol='BTCUSDT',
    start_date='2024-01-01',
    end_date='2024-12-01'
)
results = engine.run()
print(results.summary())
```

## 📈 Performance Metrics

The system calculates comprehensive performance metrics:
- **Total Return**: Overall profit/loss percentage
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Gross profit / Gross loss
- **Sharpe Ratio**: Risk-adjusted return
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Average Trade**: Mean profit/loss per trade
- **Trade Count**: Total number of trades executed

## ⚠️ Risk Disclaimer

**IMPORTANT**: Cryptocurrency trading carries significant risk. This bot is provided for educational purposes only.

- **Never invest more than you can afford to lose**
- Always test on Bybit Testnet before using real funds
- Past performance does not guarantee future results
- The developers are not responsible for any financial losses
- Use at your own risk

## 🔒 Security Best Practices

1. **Never share your API keys**
2. **Use API key restrictions**: Enable only necessary permissions (trade, read)
3. **Set IP whitelist** on Bybit API settings
4. **Start with Testnet** to validate strategies
5. **Use small position sizes** when starting
6. **Enable 2FA** on your Bybit account
7. **Keep your `.env` file secure** and never commit it to version control

## 📁 Project Structure

```
crypto-futures-bot/
├── main.py                      # Main entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── config/                      # Configuration files
├── core/                        # Core trading logic
├── strategies/                  # Trading strategies
├── backtesting/                 # Backtesting engine
├── gui/                         # GUI components
├── indicators/                  # Technical indicators
├── utils/                       # Utility functions
├── data/                        # Data storage (gitignored)
└── logs/                        # Log files (gitignored)
```

## 🛠️ Development

### Adding a New Strategy

1. Create a new file in `strategies/` inheriting from `BaseStrategy`
2. Implement `generate_signal()` method
3. Add strategy parameters to `config/strategy_params.yaml`
4. Register strategy in `strategies/__init__.py`

Example:
```python
from strategies.base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def generate_signal(self, df):
        # Your strategy logic here
        return signal  # 1 for long, -1 for short, 0 for no signal
```

### Running Tests

```bash
pytest tests/
```

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/kankanzho/crypto-futures-bot/issues)
- **Documentation**: See `docs/` folder
- **Bybit API Docs**: [Bybit Official Documentation](https://bybit-exchange.github.io/docs/v5/intro)

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Bybit](https://www.bybit.com/) for the trading API
- [pybit](https://github.com/bybit-exchange/pybit) - Official Bybit Python SDK
- [TA-Lib](https://github.com/mrjbq7/ta-lib) - Technical Analysis Library
- All contributors and the open-source community

## ⚡ Quick Start Checklist

- [ ] Install Python 3.9+
- [ ] Clone repository
- [ ] Install dependencies
- [ ] Copy `.env.example` to `.env`
- [ ] Add Bybit API credentials to `.env`
- [ ] Configure `config/config.yaml`
- [ ] Test with Testnet mode
- [ ] Run backtests
- [ ] Start with small position sizes
- [ ] Monitor and adjust strategies

---

**Happy Trading! Remember to trade responsibly.** 🎯📈
