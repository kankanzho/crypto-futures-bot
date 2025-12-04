# Contributing to Crypto Futures Trading Bot

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Code of Conduct

- Be respectful and constructive
- Help others learn and improve
- Focus on what is best for the community
- Show empathy towards other contributors

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Screenshots** (if applicable)
- **System information** (OS, Python version)
- **Log files** (from `logs/` directory)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide detailed description** of the suggested enhancement
- **Explain why this would be useful**
- **List any alternatives** you've considered

### Pull Requests

1. **Fork the repo** and create your branch from `main`
2. **Follow the coding standards** outlined below
3. **Add tests** for new features
4. **Update documentation** as needed
5. **Ensure tests pass** before submitting
6. **Write a clear commit message**

## Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/crypto-futures-bot.git
cd crypto-futures-bot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies including dev tools:
```bash
pip install -r requirements.txt
pip install pytest black flake8 mypy
```

4. Create a branch for your changes:
```bash
git checkout -b feature/your-feature-name
```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guide
- Use **4 spaces** for indentation (no tabs)
- Maximum line length: **100 characters**
- Use **type hints** where appropriate
- Write **docstrings** for all public functions/classes

### Code Formatting

Use `black` for automatic formatting:
```bash
black src/ tests/
```

### Linting

Check code with `flake8`:
```bash
flake8 src/ tests/ --max-line-length=100
```

### Type Checking

Run `mypy` for type checking:
```bash
mypy src/
```

### Naming Conventions

- **Classes**: PascalCase (`RSIStrategy`, `BacktestEngine`)
- **Functions/Methods**: snake_case (`calculate_rsi`, `get_position`)
- **Constants**: UPPER_CASE (`MAX_POSITIONS`, `API_VERSION`)
- **Private methods**: prefix with underscore (`_internal_method`)

### Documentation

- Use Google-style docstrings:

```python
def calculate_position_size(capital: float, risk: float) -> float:
    """
    Calculate position size based on risk.
    
    Args:
        capital: Available capital
        risk: Risk percentage (0-1)
    
    Returns:
        Position size in base currency
    
    Raises:
        ValueError: If risk is invalid
    """
    pass
```

## Testing

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names: `test_rsi_generates_buy_signal_when_oversold()`
- Test edge cases and error conditions
- Mock external dependencies (API calls, etc.)

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rsi_strategy.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

- Aim for **80%+ code coverage**
- All new features must include tests
- Test both success and failure cases

## Adding New Features

### New Trading Strategy

1. Create file in `src/strategies/`
2. Inherit from `BaseStrategy`
3. Implement required methods:
   - `calculate_indicators()`
   - `generate_signal()`
4. Add tests in `tests/test_your_strategy.py`
5. Add configuration to `config/strategies.yaml`
6. Update documentation

Example:
```python
from .base_strategy import BaseStrategy, SignalType
import pandas as pd

class YourStrategy(BaseStrategy):
    def __init__(self, parameters: dict):
        super().__init__("Your Strategy", parameters)
        self.param1 = parameters.get('param1', 10)
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        # Calculate your indicators
        return df
    
    def generate_signal(self, symbol: str, data: pd.DataFrame) -> SignalType:
        df = self.calculate_indicators(data)
        # Your signal logic
        return SignalType.HOLD
```

### New Risk Management Feature

1. Add to appropriate module in `src/risk_management/`
2. Follow existing patterns
3. Add comprehensive tests
4. Update configuration schema
5. Document in README

### New Exchange Integration

If adding support for another exchange:

1. Create new file in `src/exchange/`
2. Implement same interface as `BybitClient`
3. Add rate limiting and retry logic
4. Add WebSocket support if available
5. Test thoroughly on testnet
6. Update documentation

## Commit Messages

Use conventional commit format:

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(strategies): add Stochastic RSI strategy

Implements Stochastic RSI strategy with configurable
parameters and multi-timeframe support.

Closes #123
```

```
fix(risk): correct trailing stop calculation

Fixed bug where trailing stop was moving in wrong
direction for short positions.

Fixes #456
```

## Documentation

When adding features, update:

1. **README.md**: Overview and features list
2. **QUICKSTART.md**: If it affects setup/usage
3. **Code comments**: Explain complex logic
4. **Docstrings**: All public APIs
5. **Configuration files**: Add examples

## Project Structure

Understand the project organization:

```
src/
├── strategies/       # Trading strategies
├── risk_management/  # Risk management modules
├── exchange/         # Exchange integrations
├── backtesting/      # Backtest engine
├── gui/             # User interfaces
└── utils/           # Utilities and helpers
```

## Release Process

1. Version bumps follow [Semantic Versioning](https://semver.org/)
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Create pull request
6. Tag release after merge

## Getting Help

- Check existing [issues](https://github.com/kankanzho/crypto-futures-bot/issues)
- Read the [documentation](README.md)
- Ask in discussions
- Be specific about your question/problem

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Mentioned in project documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to make this project better! 🚀
