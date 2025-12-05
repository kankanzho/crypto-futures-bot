# Hybrid Crypto Futures Trading Bot

A production-ready Python trading bot that combines **YOLOv8 chart pattern recognition** with **technical analysis indicators** for automated futures trading on Bybit.

## 🎯 Features

- **AI-Powered Pattern Recognition**: Uses YOLOv8 to detect chart patterns (bull flags, head & shoulders, triangles, etc.)
- **Multi-Timeframe Analysis**: Combines 15m for entry signals and 4h for trend confirmation
- **Technical Indicators**: EMA 200 for trend, RSI for momentum, ATR for risk management
- **Risk Management**: ATR-based stop loss and take profit, funding rate checks
- **In-Memory Processing**: Chart generation without disk I/O for better performance
- **Production Ready**: Comprehensive error handling, logging, and rate limiting

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- Bybit account with API credentials
- Internet connection for API access

### Dependencies
All dependencies are listed in `requirements.txt`:
```
ccxt>=4.0.0
ultralytics>=8.0.0
mplfinance>=0.12.0
pandas>=2.0.0
numpy>=1.24.0
opencv-python>=4.8.0
Pillow>=10.0.0
python-dotenv>=1.0.0
```

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/kankanzho/crypto-futures-bot.git
cd crypto-futures-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the example environment file and edit it with your credentials:
```bash
cp .env.example .env
```

Edit `.env` file:
```bash
# Bybit API Configuration
BYBIT_API_KEY=your_actual_api_key
BYBIT_API_SECRET=your_actual_api_secret

# Trading Configuration
SYMBOL=BTC/USDT:USDT
POSITION_SIZE_USDT=50
ATR_SL_MULTIPLIER=2.0
ATR_TP_MULTIPLIER=4.0

# YOLO Configuration
YOLO_CONFIDENCE_THRESHOLD=0.7

# Risk Management
FUNDING_RATE_THRESHOLD=0.0003

# Timeframes
MAIN_TIMEFRAME=15m
TREND_TIMEFRAME=4h
```

### 4. (Optional) Add Custom YOLO Model
If you have a custom trained YOLO model for chart patterns:
```bash
mkdir -p models
# Place your model file here:
# models/best_chart_patterns.pt
```

If no custom model is found, the bot will use the YOLOv8n pretrained model.

## 💡 Usage

### Basic Usage
```bash
python bybit_yolo_bot.py
```

The bot will:
1. Load the YOLO model and connect to Bybit
2. Continuously monitor the market every 60 seconds
3. Generate chart images and detect patterns
4. Execute trades when conditions are met
5. Log all actions and decisions

### Understanding the Output
The bot provides detailed logging:
```
2024-12-05 00:00:00 - Bot initialized for BTC/USDT:USDT
2024-12-05 00:00:00 - Main timeframe: 15m, Trend timeframe: 4h
2024-12-05 00:00:01 - Fetched 200 candles for 15m
2024-12-05 00:00:01 - Fetched 200 candles for 4h
2024-12-05 00:00:02 - Indicators calculated - Price: 42500.00, EMA200: 41000.00, RSI: 55.00, ATR: 250.00
2024-12-05 00:00:03 - Detected pattern: bull_flag (confidence: 0.85)
2024-12-05 00:00:03 - 🟢 LONG CONDITIONS MET!
2024-12-05 00:00:03 - ✅ BUY order executed successfully!
```

## 📊 Trading Strategy

### Multi-Timeframe Approach
- **Main Timeframe (15m)**: Pattern detection, RSI, ATR, entry timing
- **Trend Timeframe (4h)**: EMA 200 for trend confirmation

### Long Entry Conditions
All of the following must be true:
1. ✅ Price > 4H EMA 200 (confirmed uptrend)
2. ✅ YOLO detects bullish pattern (bull_flag, double_bottom, inverse_head_and_shoulders, ascending_triangle, bullish_engulfing)
3. ✅ 15m RSI < 70 (not overbought)
4. ✅ |Funding Rate| < 0.03% (low funding pressure)

### Short Entry Conditions
All of the following must be true:
1. ✅ Price < 4H EMA 200 (confirmed downtrend)
2. ✅ YOLO detects bearish pattern (bear_flag, double_top, head_and_shoulders, descending_triangle, bearish_engulfing)
3. ✅ 15m RSI > 30 (not oversold)
4. ✅ |Funding Rate| < 0.03% (low funding pressure)

### Risk Management
- **Position Size**: Fixed USDT amount (default: $50)
- **Stop Loss**: Entry ± (ATR × 2.0)
- **Take Profit**: Entry ± (ATR × 4.0)
- **Risk/Reward Ratio**: 1:2

## 🎨 Detected Patterns

### Bullish Patterns
- `bull_flag` - Continuation pattern indicating upward momentum
- `double_bottom` - Reversal pattern signaling potential uptrend
- `inverse_head_and_shoulders` - Reversal pattern for bullish breakout
- `ascending_triangle` - Continuation pattern with higher lows
- `bullish_engulfing` - Candlestick pattern showing buying pressure

### Bearish Patterns
- `bear_flag` - Continuation pattern indicating downward momentum
- `double_top` - Reversal pattern signaling potential downtrend
- `head_and_shoulders` - Reversal pattern for bearish breakdown
- `descending_triangle` - Continuation pattern with lower highs
- `bearish_engulfing` - Candlestick pattern showing selling pressure

## 🏗️ Architecture

### Class Structure: `BybitYoloBot`

#### Key Methods

1. **Initialization**
   - `__init__()`: Load YOLO model and initialize Bybit API
   - `_load_yolo_model()`: Load custom or pretrained YOLO model
   - `_initialize_exchange()`: Setup ccxt Bybit connection

2. **Data Management**
   - `fetch_ohlcv_multi_timeframe()`: Fetch 15m and 4h OHLCV data
   - `calculate_indicators()`: Compute EMA, RSI, ATR
   - `fetch_funding_rate()`: Get current funding rate

3. **Image Processing**
   - `generate_chart_image()`: Create candlestick chart in-memory using mplfinance

4. **Pattern Detection**
   - `detect_pattern()`: Run YOLOv8 inference on chart image

5. **Trading Strategy**
   - `check_long_conditions()`: Evaluate long entry criteria
   - `check_short_conditions()`: Evaluate short entry criteria

6. **Risk Management**
   - `calculate_position_size()`: Based on fixed USDT amount
   - `calculate_sl_tp()`: ATR-based stop loss and take profit

7. **Execution**
   - `execute_trade()`: Place market orders with SL/TP

8. **Main Loop**
   - `run()`: Main trading loop with error handling

### Data Flow
```
┌─────────────────────────────────────────────────────────────┐
│ 1. Fetch Multi-Timeframe Data (15m + 4h)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Calculate Indicators (EMA, RSI, ATR)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Fetch Funding Rate                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Generate Chart Image (In-Memory)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. YOLO Pattern Detection                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Check Long/Short Conditions                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Execute Trade (if conditions met)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. Wait 60 seconds and repeat                               │
└─────────────────────────────────────────────────────────────┘
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BYBIT_API_KEY` | - | Your Bybit API key (required) |
| `BYBIT_API_SECRET` | - | Your Bybit API secret (required) |
| `SYMBOL` | BTC/USDT:USDT | Trading pair |
| `POSITION_SIZE_USDT` | 50 | Position size in USDT |
| `ATR_SL_MULTIPLIER` | 2.0 | Stop loss ATR multiplier |
| `ATR_TP_MULTIPLIER` | 4.0 | Take profit ATR multiplier |
| `YOLO_CONFIDENCE_THRESHOLD` | 0.7 | Minimum confidence for pattern detection |
| `FUNDING_RATE_THRESHOLD` | 0.0003 | Maximum absolute funding rate (0.03%) |
| `MAIN_TIMEFRAME` | 15m | Main timeframe for signals |
| `TREND_TIMEFRAME` | 4h | Trend timeframe for confirmation |

### Customization

You can adjust the strategy by modifying the configuration:

- **More Conservative**: Increase `YOLO_CONFIDENCE_THRESHOLD` to 0.8 or 0.9
- **Tighter Risk**: Decrease `ATR_SL_MULTIPLIER` to 1.5
- **Higher Targets**: Increase `ATR_TP_MULTIPLIER` to 5.0 or 6.0
- **Different Timeframes**: Change to 5m/1h or 1h/1d combinations

## 🔒 Safety Features

1. **Funding Rate Check**: Pauses trading if funding rate exceeds threshold
2. **RSI Filter**: Prevents buying overbought or selling oversold
3. **Trend Confirmation**: Requires 4H EMA 200 alignment
4. **Dynamic Stop Loss**: ATR-based to adapt to volatility
5. **Position Size Management**: Fixed USDT amount to control risk
6. **API Rate Limiting**: Built-in rate limit handling with ccxt

## ⚠️ Disclaimer

**This bot is for educational purposes only. Cryptocurrency trading carries substantial risk of loss. Never trade with money you cannot afford to lose.**

- Always test with small position sizes first
- Monitor the bot regularly
- Understand the code before running it
- Keep your API keys secure
- Use API keys with withdrawal restrictions

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on GitHub.

## 🙏 Acknowledgments

- [CCXT](https://github.com/ccxt/ccxt) - Cryptocurrency exchange trading library
- [Ultralytics](https://github.com/ultralytics/ultralytics) - YOLOv8 implementation
- [mplfinance](https://github.com/matplotlib/mplfinance) - Financial data visualization
