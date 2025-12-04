#!/bin/bash

# Quick start script for the Bybit trading bot

echo "================================================"
echo "Bybit Cryptocurrency Futures Trading Bot Setup"
echo "================================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
echo "This may take a few minutes..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your Bybit API credentials!"
    echo "   nano .env  (or use your preferred editor)"
fi

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your Bybit API credentials"
echo "2. Review configuration in config/config.yaml"
echo "3. Run the bot:"
echo "   - Backtest: python main.py --backtest"
echo "   - Live trading (testnet): python main.py"
echo "   - Live trading (mainnet): python main.py --mainnet"
echo ""
echo "For more information, see README.md"
echo ""
