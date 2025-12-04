"""
Bybit API wrapper for futures trading.
Handles REST API calls for orders, positions, and account management.
"""

from typing import Dict, List, Optional, Any
import time
import os
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
from utils.logger import get_logger
from utils.helpers import get_timestamp_ms

logger = get_logger()

# Load environment variables
load_dotenv()


class BybitAPI:
    """Wrapper for Bybit API operations."""
    
    def __init__(self, testnet: bool = True):
        """
        Initialize Bybit API client.
        
        Args:
            testnet: Whether to use testnet (True) or mainnet (False)
        """
        self.testnet = testnet
        
        # Get API credentials from environment
        api_key = os.getenv('BYBIT_API_KEY', '')
        api_secret = os.getenv('BYBIT_API_SECRET', '')
        
        # Determine if using testnet from env or parameter
        use_testnet = os.getenv('BYBIT_TESTNET', str(testnet)).lower() == 'true'
        
        # Initialize HTTP session
        self.session = HTTP(
            testnet=use_testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        
        self.rate_limit_delay = 0.1  # Delay between requests (100ms)
        self.last_request_time = 0
        
        logger.info(f"Initialized Bybit API client (Testnet: {use_testnet})")
    
    def _rate_limit(self) -> None:
        """Implement rate limiting to avoid API limits."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last_request)
        
        self.last_request_time = time.time()
    
    def get_kline(
        self,
        symbol: str,
        interval: str,
        limit: int = 200,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict]:
        """
        Get historical kline/candlestick data.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Kline interval (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
            limit: Number of candles to retrieve (max 1000)
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            
        Returns:
            List of kline data
        """
        self._rate_limit()
        
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            if start_time:
                params['start'] = start_time
            if end_time:
                params['end'] = end_time
            
            response = self.session.get_kline(**params)
            
            if response['retCode'] == 0:
                return response['result']['list']
            else:
                logger.error(f"Error fetching kline data: {response['retMsg']}")
                return []
                
        except Exception as e:
            logger.error(f"Exception in get_kline: {e}")
            return []
    
    def get_tickers(self, symbol: Optional[str] = None) -> Dict:
        """
        Get latest ticker information.
        
        Args:
            symbol: Trading symbol (optional, if None returns all)
            
        Returns:
            Ticker data
        """
        self._rate_limit()
        
        try:
            params = {'category': 'linear'}
            if symbol:
                params['symbol'] = symbol
            
            response = self.session.get_tickers(**params)
            
            if response['retCode'] == 0:
                return response['result']
            else:
                logger.error(f"Error fetching tickers: {response['retMsg']}")
                return {}
                
        except Exception as e:
            logger.error(f"Exception in get_tickers: {e}")
            return {}
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        qty: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
        close_on_trigger: bool = False,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict:
        """
        Place a new order.
        
        Args:
            symbol: Trading symbol
            side: 'Buy' or 'Sell'
            order_type: 'Market' or 'Limit'
            qty: Order quantity
            price: Order price (required for limit orders)
            time_in_force: Time in force (GTC, IOC, FOK)
            reduce_only: Reduce only flag
            close_on_trigger: Close on trigger flag
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Order response
        """
        self._rate_limit()
        
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'side': side,
                'orderType': order_type,
                'qty': str(qty),
                'timeInForce': time_in_force,
                'reduceOnly': reduce_only,
                'closeOnTrigger': close_on_trigger
            }
            
            if price and order_type == 'Limit':
                params['price'] = str(price)
            
            if stop_loss:
                params['stopLoss'] = str(stop_loss)
            
            if take_profit:
                params['takeProfit'] = str(take_profit)
            
            response = self.session.place_order(**params)
            
            if response['retCode'] == 0:
                logger.info(f"Order placed successfully: {symbol} {side} {qty}")
                return response['result']
            else:
                logger.error(f"Error placing order: {response['retMsg']}")
                return {}
                
        except Exception as e:
            logger.error(f"Exception in place_order: {e}")
            return {}
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel an existing order.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        self._rate_limit()
        
        try:
            response = self.session.cancel_order(
                category='linear',
                symbol=symbol,
                orderId=order_id
            )
            
            if response['retCode'] == 0:
                logger.info(f"Order cancelled successfully: {order_id}")
                return True
            else:
                logger.error(f"Error cancelling order: {response['retMsg']}")
                return False
                
        except Exception as e:
            logger.error(f"Exception in cancel_order: {e}")
            return False
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get current positions.
        
        Args:
            symbol: Trading symbol (optional)
            
        Returns:
            List of positions
        """
        self._rate_limit()
        
        try:
            params = {'category': 'linear'}
            if symbol:
                params['symbol'] = symbol
            
            response = self.session.get_positions(**params)
            
            if response['retCode'] == 0:
                return response['result']['list']
            else:
                logger.error(f"Error fetching positions: {response['retMsg']}")
                return []
                
        except Exception as e:
            logger.error(f"Exception in get_positions: {e}")
            return []
    
    def get_wallet_balance(self, account_type: str = "UNIFIED") -> Dict:
        """
        Get wallet balance.
        
        Args:
            account_type: Account type (UNIFIED, CONTRACT)
            
        Returns:
            Wallet balance information
        """
        self._rate_limit()
        
        try:
            response = self.session.get_wallet_balance(accountType=account_type)
            
            if response['retCode'] == 0:
                return response['result']
            else:
                logger.error(f"Error fetching wallet balance: {response['retMsg']}")
                return {}
                
        except Exception as e:
            logger.error(f"Exception in get_wallet_balance: {e}")
            return {}
    
    def set_leverage(self, symbol: str, buy_leverage: int, sell_leverage: int) -> bool:
        """
        Set leverage for a symbol.
        
        Args:
            symbol: Trading symbol
            buy_leverage: Leverage for long positions
            sell_leverage: Leverage for short positions
            
        Returns:
            True if successful, False otherwise
        """
        self._rate_limit()
        
        try:
            response = self.session.set_leverage(
                category='linear',
                symbol=symbol,
                buyLeverage=str(buy_leverage),
                sellLeverage=str(sell_leverage)
            )
            
            if response['retCode'] == 0:
                logger.info(f"Leverage set successfully: {symbol} {buy_leverage}x")
                return True
            else:
                logger.error(f"Error setting leverage: {response['retMsg']}")
                return False
                
        except Exception as e:
            logger.error(f"Exception in set_leverage: {e}")
            return False
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open orders.
        
        Args:
            symbol: Trading symbol (optional)
            
        Returns:
            List of open orders
        """
        self._rate_limit()
        
        try:
            params = {'category': 'linear'}
            if symbol:
                params['symbol'] = symbol
            
            response = self.session.get_open_orders(**params)
            
            if response['retCode'] == 0:
                return response['result']['list']
            else:
                logger.error(f"Error fetching open orders: {response['retMsg']}")
                return []
                
        except Exception as e:
            logger.error(f"Exception in get_open_orders: {e}")
            return []
    
    def close_position(self, symbol: str, side: str) -> bool:
        """
        Close an open position.
        
        Args:
            symbol: Trading symbol
            side: Position side ('Buy' for long, 'Sell' for short)
            
        Returns:
            True if successful, False otherwise
        """
        # Get current position
        positions = self.get_positions(symbol)
        
        if not positions:
            logger.warning(f"No position found for {symbol}")
            return False
        
        position = positions[0]
        size = abs(float(position.get('size', 0)))
        
        if size == 0:
            logger.warning(f"Position size is 0 for {symbol}")
            return False
        
        # Place opposite order to close
        close_side = 'Sell' if side == 'Buy' else 'Buy'
        
        result = self.place_order(
            symbol=symbol,
            side=close_side,
            order_type='Market',
            qty=size,
            reduce_only=True
        )
        
        return bool(result)
