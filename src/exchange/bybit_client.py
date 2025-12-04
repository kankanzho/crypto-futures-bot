"""
Bybit exchange client for API v5.
Handles API interactions with rate limiting and retry logic.
"""

import time
import hmac
import hashlib
from typing import Dict, Any, Optional, List
from pybit.unified_trading import HTTP
import requests
from collections import deque
from datetime import datetime, timedelta
from loguru import logger


class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, max_requests: int = 10, time_window: int = 1):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove old requests outside time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # Wait if limit reached
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self.requests.clear()
        
        self.requests.append(time.time())


class BybitClient:
    """Bybit API client with rate limiting and retry logic."""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True, 
                 rate_limit_config: Optional[Dict] = None):
        """
        Initialize Bybit client.
        
        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
            testnet: Use testnet or mainnet
            rate_limit_config: Rate limit configuration
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Initialize HTTP client
        self.client = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Rate limiting
        rate_limit_config = rate_limit_config or {}
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit_config.get('requests_per_second', 10),
            time_window=1
        )
        
        self.max_retries = rate_limit_config.get('max_retries', 3)
        self.retry_delay = rate_limit_config.get('retry_delay', 1)
        self.exponential_backoff = rate_limit_config.get('exponential_backoff', True)
        
        logger.info(f"Bybit client initialized ({'testnet' if testnet else 'mainnet'})")
    
    def _make_request(self, func, *args, **kwargs) -> Dict[str, Any]:
        """
        Make API request with rate limiting and retry logic.
        
        Args:
            func: API function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            API response
        """
        for attempt in range(self.max_retries):
            try:
                self.rate_limiter.wait_if_needed()
                response = func(*args, **kwargs)
                
                if response.get('retCode') == 0:
                    return response
                else:
                    logger.warning(f"API error: {response.get('retMsg')}")
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt if self.exponential_backoff else 1)
                        time.sleep(delay)
                    else:
                        raise Exception(f"API error: {response.get('retMsg')}")
                        
            except Exception as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt if self.exponential_backoff else 1)
                    time.sleep(delay)
                else:
                    raise
        
        raise Exception("Max retries exceeded")
    
    def get_kline(self, symbol: str, interval: str, limit: int = 200, 
                  start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[Dict]:
        """
        Get kline/candlestick data.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Kline interval ('1', '3', '5', '15', '30', '60', '120', '240', 'D', 'W', 'M')
            limit: Number of results (max 200)
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            
        Returns:
            List of kline data
        """
        response = self._make_request(
            self.client.get_kline,
            category="linear",
            symbol=symbol,
            interval=interval,
            limit=limit,
            start=start_time,
            end=end_time
        )
        
        return response.get('result', {}).get('list', [])
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get latest ticker information.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Ticker data
        """
        response = self._make_request(
            self.client.get_tickers,
            category="linear",
            symbol=symbol
        )
        
        tickers = response.get('result', {}).get('list', [])
        return tickers[0] if tickers else {}
    
    def place_order(self, symbol: str, side: str, order_type: str, qty: float,
                   price: Optional[float] = None, time_in_force: str = "GTC",
                   reduce_only: bool = False, close_on_trigger: bool = False,
                   stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Dict[str, Any]:
        """
        Place an order.
        
        Args:
            symbol: Trading pair symbol
            side: 'Buy' or 'Sell'
            order_type: 'Market' or 'Limit'
            qty: Order quantity
            price: Order price (required for Limit orders)
            time_in_force: Time in force ('GTC', 'IOC', 'FOK')
            reduce_only: Reduce only flag
            close_on_trigger: Close on trigger flag
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Order response
        """
        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": str(qty),
            "timeInForce": time_in_force,
            "reduceOnly": reduce_only,
            "closeOnTrigger": close_on_trigger
        }
        
        if price:
            params["price"] = str(price)
        if stop_loss:
            params["stopLoss"] = str(stop_loss)
        if take_profit:
            params["takeProfit"] = str(take_profit)
        
        response = self._make_request(self.client.place_order, **params)
        
        logger.info(f"Order placed: {symbol} {side} {qty} @ {price or 'Market'}")
        return response.get('result', {})
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID
            
        Returns:
            Cancellation response
        """
        response = self._make_request(
            self.client.cancel_order,
            category="linear",
            symbol=symbol,
            orderId=order_id
        )
        
        logger.info(f"Order cancelled: {order_id}")
        return response.get('result', {})
    
    def get_position(self, symbol: str) -> Dict[str, Any]:
        """
        Get current position information.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Position data
        """
        response = self._make_request(
            self.client.get_positions,
            category="linear",
            symbol=symbol
        )
        
        positions = response.get('result', {}).get('list', [])
        return positions[0] if positions else {}
    
    def get_wallet_balance(self, account_type: str = "UNIFIED") -> Dict[str, Any]:
        """
        Get wallet balance.
        
        Args:
            account_type: Account type ('UNIFIED', 'CONTRACT')
            
        Returns:
            Wallet balance data
        """
        response = self._make_request(
            self.client.get_wallet_balance,
            accountType=account_type
        )
        
        return response.get('result', {})
    
    def set_leverage(self, symbol: str, buy_leverage: int, sell_leverage: int) -> Dict[str, Any]:
        """
        Set leverage for a symbol.
        
        Args:
            symbol: Trading pair symbol
            buy_leverage: Leverage for buy side
            sell_leverage: Leverage for sell side
            
        Returns:
            Response data
        """
        response = self._make_request(
            self.client.set_leverage,
            category="linear",
            symbol=symbol,
            buyLeverage=str(buy_leverage),
            sellLeverage=str(sell_leverage)
        )
        
        logger.info(f"Leverage set: {symbol} Buy={buy_leverage}x Sell={sell_leverage}x")
        return response.get('result', {})
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open orders.
        
        Args:
            symbol: Trading pair symbol (optional, gets all if not specified)
            
        Returns:
            List of open orders
        """
        params = {"category": "linear"}
        if symbol:
            params["symbol"] = symbol
        
        response = self._make_request(self.client.get_open_orders, **params)
        
        return response.get('result', {}).get('list', [])
    
    def close_position(self, symbol: str, position_idx: int = 0) -> Dict[str, Any]:
        """
        Close a position (market order).
        
        Args:
            symbol: Trading pair symbol
            position_idx: Position index (0 for one-way mode, 1 for buy, 2 for sell in hedge mode)
            
        Returns:
            Order response
        """
        # Get current position
        position = self.get_position(symbol)
        
        if not position or float(position.get('size', 0)) == 0:
            logger.warning(f"No open position for {symbol}")
            return {}
        
        size = float(position['size'])
        side = 'Sell' if position['side'] == 'Buy' else 'Buy'
        
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type='Market',
            qty=size,
            reduce_only=True
        )
    
    def get_order_history(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Get order history.
        
        Args:
            symbol: Trading pair symbol (optional)
            limit: Number of results
            
        Returns:
            List of historical orders
        """
        params = {"category": "linear", "limit": limit}
        if symbol:
            params["symbol"] = symbol
        
        response = self._make_request(self.client.get_order_history, **params)
        
        return response.get('result', {}).get('list', [])
