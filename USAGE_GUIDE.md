# Bybit Trading Bot - Complete Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Running the Bot](#running-the-bot)
4. [Backtesting](#backtesting)
5. [Strategy Selection](#strategy-selection)
6. [Risk Management](#risk-management)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites
- Python 3.9 or higher
- Bybit account (for testnet or mainnet)
- API credentials from Bybit

### Quick Setup

1. **Clone the repository**
```bash
git clone https://github.com/kankanzho/crypto-futures-bot.git
cd crypto-futures-bot
```

2. **Run the setup script**
```bash
bash setup.sh
```

3. **Configure API credentials**
```bash
nano .env
```

Add your Bybit API credentials:
```
BYBIT_API_KEY=your_actual_api_key
BYBIT_API_SECRET=your_actual_api_secret
BYBIT_TESTNET=true
```

### Manual Installation

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API credentials
nano .env
```

## Configuration

### Main Configuration (`config/config.yaml`)

```yaml
trading:
  mode: testnet              # testnet or mainnet
  leverage: 10               # Leverage multiplier (1-20)
  max_positions: 4           # Maximum concurrent positions
  position_size_pct: 25      # Position size as % of capital

risk_management:
  stop_loss_pct: 2.0        # Stop loss percentage
  take_profit_pct: 3.0      # Take profit percentage
  trailing_stop: true       # Enable trailing stop
  max_daily_loss_pct: 5.0   # Maximum daily loss limit

strategies:
  active_strategy: scalping  # Strategy to use
  volume_filter: true        # Enable volume filtering
  volatility_filter: true    # Enable volatility filtering
```

### Strategy Parameters (`config/strategy_params.yaml`)

Each strategy has customizable parameters:

```yaml
scalping:
  timeframe: "1"           # 1 minute candles
  fast_ema: 5
  slow_ema: 13
  rsi_period: 14

rsi:
  timeframe: "3"           # 3 minute candles
  rsi_oversold: 30
  rsi_overbought: 70
```

### Coin Selection (`config/coins.yaml`)

Enable/disable trading pairs:

```yaml
coins:
  - symbol: BTCUSDT
    enabled: true
    allocation_pct: 25
    
  - symbol: ETHUSDT
    enabled: true
    allocation_pct: 25
```

## Running the Bot

### Testnet Mode (Recommended for testing)

```bash
python main.py
```

This runs the bot on Bybit testnet with paper trading.

### Mainnet Mode (Real money)

⚠️ **WARNING**: This uses real money!

```bash
python main.py --mainnet
```

You will be prompted to confirm before proceeding.

### With GUI (Stub version)

```bash
python main.py --gui
```

Note: Full GUI implementation is in progress. Currently shows a placeholder.

## Backtesting

Run historical strategy testing:

```bash
python main.py --backtest
```

This will:
1. Load historical data from Bybit
2. Test multiple strategies
3. Display performance metrics

### Backtest Configuration

Edit `config/config.yaml`:

```yaml
backtesting:
  start_date: "2024-01-01"
  end_date: "2024-12-01"
  initial_capital: 10000
  commission: 0.075
  slippage: 0.05
```

### Example Backtest Output

```
Testing Scalping Strategy...
----------------------------------------
Initial Capital: $10,000.00
Final Capital: $11,500.00
Total Return: $1,500.00 (15.00%)
Total Trades: 150
Win Rate: 62.00%
Profit Factor: 1.85
Max Drawdown: 8.50%
```

## Strategy Selection

### Available Strategies

1. **Scalping** - High-frequency short-term trades
   - Best for: 1-minute timeframes
   - Signals: EMA crossovers + RSI + volume

2. **RSI** - Mean reversion strategy
   - Best for: Range-bound markets
   - Signals: Overbought/oversold conditions

3. **MACD** - Trend following
   - Best for: Trending markets
   - Signals: MACD line crossovers

4. **Bollinger Bands** - Volatility breakout
   - Best for: Volatile markets
   - Signals: Price bounces off bands

5. **Momentum** - Rate of change
   - Best for: Strong trends
   - Signals: Strong momentum shifts

6. **EMA Cross** - Moving average crossover
   - Best for: Clear trends
   - Signals: Fast/slow EMA crosses

7. **Combined** - Multi-strategy ensemble
   - Best for: Robust performance
   - Signals: Weighted combination

### Switching Strategies

Edit `config/config.yaml`:

```yaml
strategies:
  active_strategy: rsi  # Change to desired strategy
```

Available values: `scalping`, `rsi`, `macd`, `bollinger`, `momentum`, `ema_cross`, `combined`

## Risk Management

### Position Sizing

The bot automatically calculates position size based on:
- Account balance
- Risk per trade (2% default)
- Stop loss distance
- Leverage

### Stop Loss and Take Profit

Configured in `config/config.yaml`:

```yaml
risk_management:
  stop_loss_pct: 2.0       # 2% stop loss
  take_profit_pct: 3.0     # 3% take profit
  trailing_stop: true      # Enable trailing stop
  trailing_stop_pct: 1.5   # Trail by 1.5%
```

### Daily Loss Limit

The bot will stop trading if daily loss exceeds the limit:

```yaml
risk_management:
  max_daily_loss_pct: 5.0  # Stop if -5% daily loss
```

### Leverage Management

Set leverage for all positions:

```yaml
trading:
  leverage: 10  # 10x leverage
```

⚠️ Higher leverage = higher risk!

## Monitoring

### Log Files

Logs are saved to `logs/trading_bot.log`:

```bash
tail -f logs/trading_bot.log
```

### Log Levels

Configure in `.env`:

```
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Position Tracking

The bot logs:
- Trade entries with price and quantity
- Trade exits with P&L
- Stop loss and take profit hits
- Daily P&L summary

Example log output:
```
2024-12-04 10:30:15 | INFO | Position added: BTCUSDT long 0.05 @ 42500
2024-12-04 10:45:20 | INFO | Position closed: BTCUSDT | Reason: take_profit | P&L: $63.75 (+3.00%)
```

## Troubleshooting

### Common Issues

#### 1. API Connection Error

**Problem**: Cannot connect to Bybit API

**Solution**:
- Check your API credentials in `.env`
- Verify API key has necessary permissions (trade, read)
- Check if using correct mode (testnet/mainnet)
- Verify internet connection

#### 2. Import Errors

**Problem**: `ModuleNotFoundError` when running

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 3. No Trades Executing

**Problem**: Bot runs but no trades are executed

**Solution**:
- Check if coins are enabled in `config/coins.yaml`
- Verify strategy is generating signals (check logs)
- Ensure filters aren't too restrictive
- Check if daily loss limit was hit

#### 4. TA-Lib Installation Error

**Problem**: Cannot install TA-Lib

**Solution** (Ubuntu/Debian):
```bash
sudo apt-get install build-essential wget
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install TA-Lib
```

**Solution** (macOS):
```bash
brew install ta-lib
pip install TA-Lib
```

**Solution** (Windows):
Download pre-built wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

### Debug Mode

Enable debug logging for more detailed output:

```bash
# Edit .env
LOG_LEVEL=DEBUG
```

### Getting Help

1. Check the logs: `tail -f logs/trading_bot.log`
2. Review configuration files
3. Test with backtest mode first
4. Start with testnet before mainnet
5. Open an issue on GitHub with:
   - Error message
   - Log excerpt
   - Configuration (without API keys!)

## Best Practices

### 1. Start with Testnet
Always test your configuration on testnet before using real money.

### 2. Run Backtests
Backtest strategies on historical data to validate performance.

### 3. Start Small
Use small position sizes when starting with real money.

### 4. Monitor Regularly
Check the bot's performance and logs regularly.

### 5. Set Appropriate Limits
Configure realistic stop losses and position sizes.

### 6. Diversify
Don't put all capital in one coin or strategy.

### 7. Stay Updated
Keep the bot updated and monitor for API changes.

## Advanced Usage

### Custom Strategy Development

Create a new strategy by inheriting from `BaseStrategy`:

```python
# strategies/my_custom_strategy.py
from strategies.base_strategy import BaseStrategy, Signal

class MyCustomStrategy(BaseStrategy):
    def __init__(self, params=None):
        super().__init__('my_custom', params)
    
    def generate_signal(self, df):
        # Your strategy logic here
        if condition_for_long:
            return Signal(Signal.LONG, strength=0.8, reason="My reason")
        return Signal(Signal.NEUTRAL, reason="No signal")
```

### Parameter Optimization

Use the optimizer to find best parameters:

```python
from backtesting.optimizer import ParameterOptimizer
from strategies.rsi_strategy import RSIStrategy

param_grid = {
    'rsi_oversold': [20, 25, 30],
    'rsi_overbought': [70, 75, 80]
}

result = ParameterOptimizer.grid_search(
    RSIStrategy,
    param_grid,
    historical_data
)
```

## Safety Reminders

⚠️ **IMPORTANT SAFETY INFORMATION**:

1. **Never invest more than you can afford to lose**
2. **Cryptocurrency trading carries significant risk**
3. **Past performance does not guarantee future results**
4. **Always use stop losses**
5. **Start with testnet and small amounts**
6. **Keep your API keys secure**
7. **Monitor your positions regularly**
8. **Understand the strategies before using them**

## Support

- **Documentation**: See README.md and this guide
- **Issues**: https://github.com/kankanzho/crypto-futures-bot/issues
- **Bybit API Docs**: https://bybit-exchange.github.io/docs/v5/intro

---

**Disclaimer**: This software is for educational purposes. The developers are not responsible for any financial losses. Trade at your own risk.
