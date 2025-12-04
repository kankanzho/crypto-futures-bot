#!/usr/bin/env python3
"""
Verify the trading bot installation and configuration.
This script checks if all files and configurations are in place.
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✓ {description}")
        return True
    else:
        print(f"✗ {description} - NOT FOUND")
        return False


def check_directory_structure():
    """Verify directory structure."""
    print("\n" + "=" * 60)
    print("Checking Directory Structure")
    print("=" * 60)
    
    directories = [
        ('config', 'Configuration directory'),
        ('core', 'Core modules directory'),
        ('strategies', 'Trading strategies directory'),
        ('backtesting', 'Backtesting modules directory'),
        ('gui', 'GUI components directory'),
        ('indicators', 'Technical indicators directory'),
        ('utils', 'Utility modules directory'),
    ]
    
    all_exist = True
    for dir_name, description in directories:
        exists = check_file_exists(dir_name, f"{description}: {dir_name}/")
        all_exist = all_exist and exists
    
    return all_exist


def check_config_files():
    """Verify configuration files."""
    print("\n" + "=" * 60)
    print("Checking Configuration Files")
    print("=" * 60)
    
    config_files = [
        ('config/config.yaml', 'Main configuration'),
        ('config/strategy_params.yaml', 'Strategy parameters'),
        ('config/coins.yaml', 'Coin configuration'),
        ('.env.example', 'Environment template'),
    ]
    
    all_exist = True
    for filepath, description in config_files:
        exists = check_file_exists(filepath, f"{description}: {filepath}")
        all_exist = all_exist and exists
    
    # Check if .env exists
    if os.path.exists('.env'):
        print("✓ Environment file: .env")
        print("  ⚠️  Remember to add your API credentials!")
    else:
        print("✗ Environment file: .env - NOT FOUND")
        print("  Run: cp .env.example .env")
        all_exist = False
    
    return all_exist


def check_core_modules():
    """Verify core module files."""
    print("\n" + "=" * 60)
    print("Checking Core Modules")
    print("=" * 60)
    
    modules = [
        ('core/bybit_api.py', 'Bybit API wrapper'),
        ('core/bot.py', 'Main bot logic'),
        ('core/order_manager.py', 'Order manager'),
        ('core/position_manager.py', 'Position manager'),
        ('core/risk_manager.py', 'Risk manager'),
        ('core/websocket_client.py', 'WebSocket client'),
    ]
    
    all_exist = True
    for filepath, description in modules:
        exists = check_file_exists(filepath, f"{description}: {filepath}")
        all_exist = all_exist and exists
    
    return all_exist


def check_strategies():
    """Verify strategy files."""
    print("\n" + "=" * 60)
    print("Checking Trading Strategies")
    print("=" * 60)
    
    strategies = [
        ('strategies/base_strategy.py', 'Base strategy class'),
        ('strategies/scalping_strategy.py', 'Scalping strategy'),
        ('strategies/rsi_strategy.py', 'RSI strategy'),
        ('strategies/macd_strategy.py', 'MACD strategy'),
        ('strategies/bollinger_strategy.py', 'Bollinger Bands strategy'),
        ('strategies/momentum_strategy.py', 'Momentum strategy'),
        ('strategies/ema_cross_strategy.py', 'EMA Cross strategy'),
        ('strategies/strategy_combiner.py', 'Strategy combiner'),
    ]
    
    all_exist = True
    for filepath, description in strategies:
        exists = check_file_exists(filepath, f"{description}: {filepath}")
        all_exist = all_exist and exists
    
    return all_exist


def check_dependencies():
    """Check if key dependencies can be imported."""
    print("\n" + "=" * 60)
    print("Checking Python Dependencies")
    print("=" * 60)
    
    dependencies = [
        ('pandas', 'Data manipulation'),
        ('numpy', 'Numerical computing'),
        ('pybit', 'Bybit API client'),
        ('ta', 'Technical analysis'),
        ('dotenv', 'Environment variables'),
        ('loguru', 'Logging'),
        ('yaml', 'YAML configuration'),
    ]
    
    all_installed = True
    for module_name, description in dependencies:
        try:
            if module_name == 'dotenv':
                __import__('dotenv')
            elif module_name == 'yaml':
                __import__('yaml')
            else:
                __import__(module_name)
            print(f"✓ {description}: {module_name}")
        except ImportError:
            print(f"✗ {description}: {module_name} - NOT INSTALLED")
            all_installed = False
    
    if not all_installed:
        print("\n  Install missing dependencies:")
        print("  pip install -r requirements.txt")
    
    return all_installed


def check_python_version():
    """Check Python version."""
    print("\n" + "=" * 60)
    print("Checking Python Version")
    print("=" * 60)
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"Python version: {version_str}")
    
    if version.major >= 3 and version.minor >= 9:
        print("✓ Python version is compatible (3.9+)")
        return True
    else:
        print("✗ Python version is too old (requires 3.9+)")
        return False


def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("Bybit Trading Bot - Installation Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version()),
        ("Directory Structure", check_directory_structure()),
        ("Configuration Files", check_config_files()),
        ("Core Modules", check_core_modules()),
        ("Trading Strategies", check_strategies()),
        ("Python Dependencies", check_dependencies()),
    ]
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {check_name}")
        all_passed = all_passed and passed
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All checks passed! The bot is ready to use.")
        print("\nNext steps:")
        print("1. Edit .env and add your Bybit API credentials")
        print("2. Review config/config.yaml")
        print("3. Run backtest: python main.py --backtest")
        print("4. Run bot: python main.py")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Run setup.sh to install dependencies")
        print("- Copy .env.example to .env")
        print("- Install Python 3.9 or higher")
    
    print()
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
