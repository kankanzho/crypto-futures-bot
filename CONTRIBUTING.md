# Contributing to Crypto Futures Bot

Thank you for your interest in contributing to the Crypto Futures Bot! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/crypto-futures-bot.git`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a feature branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests to verify setup
python -m unittest discover -s tests -p 'test_*.py'
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and concise
- Add comments for complex logic

### Example
```python
def analyze_market(df: pd.DataFrame) -> MarketCondition:
    """
    Analyze market conditions from OHLCV data.
    
    Args:
        df: DataFrame with OHLCV columns
        
    Returns:
        MarketCondition object with analysis results
        
    Raises:
        ValueError: If DataFrame is invalid
    """
    # Implementation here
    pass
```

## Testing

### Running Tests
```bash
# Run all tests
python -m unittest discover -s tests -p 'test_*.py' -v

# Run specific test file
python -m unittest tests.test_market_analyzer -v

# Run specific test
python -m unittest tests.test_market_analyzer.TestMarketAnalyzer.test_analyze_returns_market_condition
```

### Writing Tests
- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern

Example:
```python
def test_strategy_selection_high_volatility(self):
    """Test strategy selection for high volatility conditions."""
    # Arrange
    condition = MarketCondition(
        volatility='HIGH',
        trend='STRONG_UP',
        volume='HIGH',
        timestamp=datetime.now()
    )
    
    # Act
    strategy, score = self.selector.select_best(condition)
    
    # Assert
    self.assertIn(strategy, ['momentum', 'macd', 'bollinger'])
    self.assertGreaterEqual(score, 70)
```

## Pull Request Process

1. **Update your branch** with the latest main:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests** and ensure they pass:
   ```bash
   python -m unittest discover -s tests -p 'test_*.py'
   ```

3. **Commit your changes** with clear messages:
   ```bash
   git commit -m "Add feature: description of feature"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub:
   - Provide a clear title and description
   - Reference any related issues
   - Include screenshots for UI changes
   - List any breaking changes

6. **Respond to feedback** and make requested changes

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
Add market volatility classification

- Implement ATR calculation
- Add Bollinger Bandwidth measurement
- Create volatility level classification
```

Format:
- First line: Brief summary (50 chars or less)
- Blank line
- Detailed description with bullet points

## Areas for Contribution

### High Priority
- [ ] Real exchange integration (Binance, Bybit, etc.)
- [ ] Comprehensive backtesting engine
- [ ] Performance optimization
- [ ] Additional technical indicators

### Medium Priority
- [ ] GUI dashboard
- [ ] Machine learning strategy optimization
- [ ] Multi-pair support
- [ ] Advanced risk management

### Good First Issues
- [ ] Documentation improvements
- [ ] Additional tests
- [ ] Code style cleanup
- [ ] Example scripts

## Code Review Process

All submissions require review:
1. Automated tests must pass
2. Code must follow style guidelines
3. Changes must be documented
4. At least one maintainer approval required

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Email: rhrhksgh10@naver.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
