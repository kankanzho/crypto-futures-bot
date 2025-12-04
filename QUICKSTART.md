# Quick Start Guide

This guide will help you get the Crypto Futures Trading Bot up and running quickly.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Bybit account (testnet recommended for testing)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/kankanzho/crypto-futures-bot.git
cd crypto-futures-bot
```

### 2. Create Virtual Environment

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Credentials

Create a `.env` file from the example:

```bash
cp config/.env.example .env
```

Edit `.env` with your Bybit API credentials:

```env
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET=true
INITIAL_CAPITAL=10000
```

**Getting API Keys:**
1. Go to [Bybit Testnet](https://testnet.bybit.com/) (or mainnet)
2. Sign up/Login
3. Go to API Management
4. Create new API key
5. Copy API key and secret to `.env`

### 5. Configure Trading Settings

Edit `config/config.yaml` to customize:
- Active coins and allocations
- Risk management parameters
- Leverage settings
- Position sizing method

Edit `config/strategies.yaml` to customize:
- Strategy parameters
- Stop loss settings
- Take profit targets

## Running the Bot

### Run Backtesting Example

Before running live, test strategies with backtest:

```bash
python examples/backtest_example.py
```

This will:
- Generate sample data
- Run RSI strategy backtest
- Display performance metrics

### Run GUI Dashboard

Launch the Streamlit dashboard:

```bash
streamlit run src/gui/dashboard.py
```

Access at: `http://localhost:8501`

### Run Live Trading Bot

**⚠️ Only after thorough testing on testnet!**

```bash
python src/main.py
```

The bot will:
1. Connect to Bybit API
2. Subscribe to market data
3. Execute configured strategy
4. Manage positions with stop loss/take profit

## Running Tests

Run unit tests to verify everything works:

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rsi_strategy.py -v
```

## Project Structure Overview

```
crypto-futures-bot/
├── config/              # Configuration files
│   ├── config.yaml      # Main bot config
│   ├── strategies.yaml  # Strategy parameters
│   └── .env.example     # API credentials template
├── src/                 # Source code
│   ├── strategies/      # Trading strategies
│   ├── risk_management/ # Stop loss, take profit, position sizing
│   ├── exchange/        # Bybit API integration
│   ├── backtesting/     # Backtest engine
│   ├── gui/            # Dashboard
│   ├── utils/          # Utilities
│   └── main.py         # Main bot runner
├── tests/              # Unit tests
├── examples/           # Example scripts
└── data/               # Historical data storage
```

## Common Tasks

### Change Strategy

Edit `src/main.py`, line ~120:
```python
active_strategy = "rsi"  # Change to: macd, bollinger, ema_cross
```

### Adjust Risk Parameters

Edit `config/strategies.yaml`:
```yaml
rsi:
  stop_loss:
    type: "percentage"
    value: 0.02  # Change stop loss %
  take_profit:
    ratio: 2.0   # Change risk/reward ratio
```

### Add New Coin

Edit `config/config.yaml`:
```yaml
coins:
  - symbol: "SOLUSDT"
    allocation: 0.2
    leverage: 8
    enabled: true
```

### Change Position Sizing

Edit `config/config.yaml`:
```yaml
position_sizing:
  method: "fixed_risk"     # or "kelly_criterion"
  risk_per_trade: 0.02     # Risk 2% per trade
```

## Troubleshooting

### "Module not found" errors

```bash
# Make sure you're in virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### API connection errors

- Check API credentials in `.env`
- Verify testnet/mainnet setting matches your API key
- Check internet connection
- Ensure API key has necessary permissions

### Insufficient data errors

The bot needs at least 100 candles for indicators. Wait a few minutes after starting or fetch historical data first.

### Rate limit errors

Reduce request frequency in `config/config.yaml`:
```yaml
api:
  rate_limit:
    requests_per_second: 5  # Reduce from 10
```

## Next Steps

1. ✅ Run backtest example to understand performance metrics
2. ✅ Test on Bybit testnet with small amounts
3. ✅ Monitor in dashboard for at least a day
4. ✅ Review logs in `logs/` directory
5. ✅ Adjust strategy parameters based on results
6. ⚠️ Only go live after thorough testing!

## Safety Checklist

Before going live:
- [ ] Tested extensively on testnet
- [ ] Understand all strategy parameters
- [ ] Set appropriate risk limits
- [ ] Enabled IP whitelist on Bybit
- [ ] Set API key with minimum required permissions
- [ ] Started with small capital
- [ ] Monitoring system is in place
- [ ] Emergency stop procedure is clear

## Support

- Check [README.md](README.md) for detailed documentation
- Review code comments in source files
- Open GitHub issues for bugs
- Test on testnet before asking for help

## Disclaimer

Trading cryptocurrency futures is highly risky. This bot is for educational purposes. Use at your own risk. The creators are not responsible for any financial losses.

---

**Ready to start? Run the backtest example first:**

```bash
python examples/backtest_example.py
```

Good luck and trade responsibly! 🚀
