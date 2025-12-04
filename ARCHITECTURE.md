# Project Architecture Documentation

## Overview
This document provides a comprehensive overview of the Bybit cryptocurrency futures trading bot architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Main Entry Point                        │
│                        (main.py)                             │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼─────┐          ┌─────▼──────┐
    │   GUI    │          │  Trading   │
    │  System  │          │    Bot     │
    └──────────┘          └─────┬──────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
         ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
         │ Bybit   │      │Strategy │      │  Risk   │
         │   API   │      │ Engine  │      │ Manager │
         └─────────┘      └─────────┘      └─────────┘
```

## Module Structure

### Core Modules (`core/`)

#### `bot.py` - Main Trading Bot
- **Purpose**: Orchestrates all trading operations
- **Key Functions**:
  - `start()`: Start trading loop
  - `stop()`: Stop trading
  - `_process_symbol()`: Process trading logic for each symbol
  - `_check_entry_signal()`: Check for entry opportunities
  - `_manage_position()`: Manage open positions
  - `emergency_close_all()`: Emergency position closure

#### `bybit_api.py` - API Client
- **Purpose**: REST API wrapper for Bybit
- **Key Functions**:
  - `get_kline()`: Fetch historical price data
  - `place_order()`: Place trading orders
  - `get_positions()`: Retrieve open positions
  - `get_wallet_balance()`: Get account balance
  - `set_leverage()`: Configure leverage

#### `websocket_client.py` - Real-time Data
- **Purpose**: WebSocket client for live market data
- **Key Functions**:
  - `connect()`: Establish WebSocket connection
  - `subscribe_kline()`: Subscribe to candlestick updates
  - `subscribe_ticker()`: Subscribe to ticker updates

#### `order_manager.py` - Order Management
- **Purpose**: Handle order creation and tracking
- **Key Classes**:
  - `Order`: Order data structure
  - `OrderManager`: Order lifecycle management

#### `position_manager.py` - Position Tracking
- **Purpose**: Track and manage open positions
- **Key Classes**:
  - `Position`: Position data structure
  - `PositionManager`: Position lifecycle management

#### `risk_manager.py` - Risk Control
- **Purpose**: Implement risk management rules
- **Key Functions**:
  - `calculate_position_size()`: Determine trade size
  - `calculate_stop_loss()`: Calculate SL price
  - `calculate_take_profit()`: Calculate TP price
  - `update_trailing_stop()`: Update trailing stops
  - `validate_order()`: Validate order before placement

### Strategy System (`strategies/`)

#### Base Strategy Pattern
All strategies inherit from `BaseStrategy` and implement:
- `generate_signal()`: Core signal generation logic
- Built-in filters: volume, volatility, trend

#### Available Strategies

1. **Scalping Strategy**
   - Timeframe: 1 minute
   - Indicators: EMA(5), EMA(13), RSI(14), Volume
   - Entry: EMA crossover with RSI and volume confirmation

2. **RSI Strategy**
   - Timeframe: 3 minutes
   - Indicators: RSI(14)
   - Entry: Oversold/overbought reversals

3. **MACD Strategy**
   - Timeframe: 5 minutes
   - Indicators: MACD(12,26,9)
   - Entry: MACD line crosses signal line

4. **Bollinger Bands Strategy**
   - Timeframe: 3 minutes
   - Indicators: BB(20, 2)
   - Entry: Price bounces off bands

5. **Momentum Strategy**
   - Timeframe: 5 minutes
   - Indicators: ROC(10), Volume
   - Entry: Strong momentum with volume

6. **EMA Cross Strategy**
   - Timeframe: 3 minutes
   - Indicators: EMA(9), EMA(21), EMA(50)
   - Entry: Fast/slow EMA crossover with trend filter

7. **Combined Strategy**
   - Uses multiple strategies
   - Weighted voting system
   - Requires minimum confirmations

### Technical Indicators (`indicators/`)

#### `technical_indicators.py`
Implements standard indicators:
- Moving Averages (EMA, SMA)
- Oscillators (RSI, Stochastic)
- Trend (MACD, ADX)
- Volatility (Bollinger Bands, ATR)
- Volume (VWAP, Volume MA)

#### `custom_indicators.py`
Advanced custom indicators:
- Support/Resistance detection
- Trend strength calculation
- Volatility ratio
- Volume profile
- Order flow imbalance
- Money Flow Index
- Squeeze momentum
- Composite index

### Backtesting System (`backtesting/`)

#### `data_loader.py`
- Loads historical data from Bybit
- Calculates technical indicators
- Prepares data for backtesting

#### `backtest_engine.py`
- Simulates trading with historical data
- Accounts for commissions and slippage
- Tracks equity curve and trades

#### `performance_analyzer.py`
- Calculates performance metrics
- Sharpe ratio, max drawdown
- Win rate, profit factor

#### `optimizer.py`
- Grid search for parameter optimization
- Finds best strategy parameters

### Utility Modules (`utils/`)

#### `logger.py`
- Configures logging with loguru
- File and console output
- Log rotation and retention

#### `config_loader.py`
- Loads YAML configuration files
- Provides config access interface
- Supports hot-reloading

#### `helpers.py`
- Position sizing calculations
- P&L calculations
- Time and formatting utilities
- Validation functions

#### `notifications.py`
- Trade entry/exit notifications
- Error and warning alerts
- Sound and popup support

### GUI System (`gui/`)

Currently stub implementations for future development:
- `main_window.py`: Main application window
- `dashboard_widget.py`: Dashboard display
- `chart_widget.py`: Price charts
- `position_widget.py`: Position table
- `log_widget.py`: Log viewer
- `control_panel.py`: Bot controls
- `backtest_window.py`: Backtest interface

## Data Flow

### Live Trading Flow

```
1. Bot starts → Initialize components
2. Load configuration
3. Connect to Bybit (API + WebSocket)
4. For each trading symbol:
   a. Fetch latest market data
   b. Calculate technical indicators
   c. Generate trading signal
   d. If signal:
      - Validate with risk manager
      - Calculate position size
      - Place order via order manager
   e. If position exists:
      - Update with current price
      - Check stop loss / take profit
      - Update trailing stop
5. Sleep and repeat
```

### Backtesting Flow

```
1. Load historical data
2. Calculate indicators
3. For each candle:
   a. Generate signal from strategy
   b. If no position and signal:
      - Enter position
      - Apply slippage and commission
   c. If position exists:
      - Check exit conditions
      - Close position if triggered
4. Calculate performance metrics
5. Display results
```

## Configuration Hierarchy

```
.env                          # API credentials (git-ignored)
├── config/
│   ├── config.yaml          # Main configuration
│   ├── strategy_params.yaml # Strategy parameters
│   └── coins.yaml           # Trading pairs
```

## Risk Management Flow

```
New Trade Request
    ↓
Can Open Position?
    ├─ Check daily loss limit
    ├─ Check max positions
    └─ Check capital availability
    ↓
Calculate Position Size
    ├─ Risk per trade (2%)
    ├─ Stop loss distance
    └─ Apply leverage
    ↓
Calculate Stop Loss
    ├─ Percentage-based OR
    └─ ATR-based
    ↓
Calculate Take Profit
    ├─ Percentage-based OR
    └─ Risk-reward ratio
    ↓
Validate Order
    ├─ Check order value
    ├─ Check quantity
    └─ Final approval
    ↓
Place Order
```

## Error Handling Strategy

### API Errors
- Automatic retry with exponential backoff
- Rate limit monitoring and throttling
- Graceful degradation on API failures

### Trading Errors
- Order validation before placement
- Position reconciliation
- Emergency close all functionality

### Data Errors
- NaN value checking
- Data completeness validation
- Fallback to cached data

## Performance Considerations

### Optimization Techniques
1. **Rate Limiting**: Prevents API ban
2. **Data Caching**: Reduces API calls
3. **Asynchronous Operations**: WebSocket for real-time data
4. **Efficient Indicators**: Vectorized calculations with pandas/numpy

### Scalability
- Supports multiple symbols concurrently
- Configurable update intervals
- Modular architecture for easy extension

## Security Measures

1. **API Key Management**
   - Stored in .env (git-ignored)
   - Never logged or displayed
   - Restricted permissions recommended

2. **Risk Controls**
   - Position size limits
   - Daily loss limits
   - Leverage caps
   - Emergency shutdown

3. **Data Validation**
   - Input validation on all external data
   - Type checking with type hints
   - Comprehensive error handling

## Testing Strategy

### Unit Tests (Recommended)
- Test individual functions
- Mock external dependencies
- Validate calculations

### Integration Tests (Recommended)
- Test component interactions
- Use testnet for API testing
- Validate data flow

### Backtesting
- Historical performance validation
- Parameter optimization
- Strategy comparison

## Deployment Recommendations

### Development Environment
1. Use testnet
2. Enable debug logging
3. Small position sizes
4. Test all strategies

### Production Environment
1. Use mainnet (carefully!)
2. Info-level logging
3. Appropriate position sizing
4. Monitor continuously
5. Start with one strategy

## Future Enhancements

### Planned Features
1. Full GUI implementation with PyQt5
2. Advanced charting with real-time updates
3. Machine learning integration
4. Multi-exchange support
5. Advanced order types (trailing, OCO)
6. Telegram/Discord notifications
7. Cloud deployment support
8. Database for trade history
9. Advanced analytics dashboard
10. Strategy backtesting optimization

### Extensibility Points
- New strategies: Inherit from `BaseStrategy`
- New indicators: Add to `indicators/`
- Custom risk rules: Extend `RiskManager`
- Additional exchanges: Implement API interface

## Maintenance

### Regular Tasks
1. Update dependencies
2. Monitor API changes
3. Review and optimize strategies
4. Analyze trading performance
5. Backup configuration and logs

### Monitoring
- Check logs daily
- Review P&L regularly
- Monitor API rate limits
- Validate position accuracy

## License and Disclaimer

This software is for educational purposes only. Cryptocurrency trading involves substantial risk of loss. Use at your own risk. The developers assume no liability for any financial losses incurred.

---

**Last Updated**: December 2024
**Version**: 1.0.0
