"""
WebSocket handler for real-time market data from Bybit.
"""

import json
import asyncio
import websockets
from typing import Callable, Dict, Any, List, Optional
from loguru import logger
from datetime import datetime


class BybitWebSocket:
    """WebSocket client for Bybit real-time data."""
    
    def __init__(self, testnet: bool = True, on_message: Optional[Callable] = None,
                 ping_interval: int = 20, max_reconnect_attempts: int = 10,
                 reconnect_delay: int = 5):
        """
        Initialize WebSocket client.
        
        Args:
            testnet: Use testnet or mainnet
            on_message: Callback function for messages
            ping_interval: Ping interval in seconds
            max_reconnect_attempts: Maximum reconnection attempts
            reconnect_delay: Delay between reconnection attempts
        """
        self.testnet = testnet
        self.base_url = "wss://stream-testnet.bybit.com/v5/public/linear" if testnet else "wss://stream.bybit.com/v5/public/linear"
        
        self.on_message = on_message
        self.ping_interval = ping_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        
        self.ws = None
        self.subscriptions: List[Dict[str, Any]] = []
        self.is_connected = False
        self.reconnect_count = 0
        
        logger.info(f"WebSocket handler initialized ({'testnet' if testnet else 'mainnet'})")
    
    async def connect(self):
        """Establish WebSocket connection."""
        try:
            self.ws = await websockets.connect(self.base_url)
            self.is_connected = True
            self.reconnect_count = 0
            logger.info("WebSocket connected")
            
            # Resubscribe to previous subscriptions
            for sub in self.subscriptions:
                await self._send(sub)
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
            self.is_connected = False
            logger.info("WebSocket disconnected")
    
    async def _send(self, message: Dict[str, Any]):
        """
        Send message through WebSocket.
        
        Args:
            message: Message to send
        """
        if self.ws and self.is_connected:
            await self.ws.send(json.dumps(message))
    
    async def subscribe(self, topics: List[str]):
        """
        Subscribe to topics.
        
        Args:
            topics: List of topics to subscribe to
        """
        message = {
            "op": "subscribe",
            "args": topics
        }
        
        self.subscriptions.append(message)
        await self._send(message)
        logger.info(f"Subscribed to topics: {topics}")
    
    async def unsubscribe(self, topics: List[str]):
        """
        Unsubscribe from topics.
        
        Args:
            topics: List of topics to unsubscribe from
        """
        message = {
            "op": "unsubscribe",
            "args": topics
        }
        
        # Remove from subscriptions
        self.subscriptions = [s for s in self.subscriptions if s.get('args') != topics]
        
        await self._send(message)
        logger.info(f"Unsubscribed from topics: {topics}")
    
    async def _ping(self):
        """Send ping to keep connection alive."""
        while self.is_connected:
            try:
                await self._send({"op": "ping"})
                await asyncio.sleep(self.ping_interval)
            except Exception as e:
                logger.error(f"Ping failed: {e}")
                break
    
    async def _handle_messages(self):
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.ws:
                data = json.loads(message)
                
                # Handle pong
                if data.get('op') == 'pong':
                    continue
                
                # Handle subscription response
                if data.get('op') == 'subscribe':
                    if data.get('success'):
                        logger.debug(f"Subscription successful: {data.get('ret_msg')}")
                    else:
                        logger.error(f"Subscription failed: {data.get('ret_msg')}")
                    continue
                
                # Handle data messages
                if self.on_message:
                    try:
                        await self.on_message(data)
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")
                        
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error handling messages: {e}")
            self.is_connected = False
    
    async def _reconnect(self):
        """Attempt to reconnect WebSocket."""
        while self.reconnect_count < self.max_reconnect_attempts:
            try:
                logger.info(f"Reconnection attempt {self.reconnect_count + 1}/{self.max_reconnect_attempts}")
                await asyncio.sleep(self.reconnect_delay)
                await self.connect()
                return True
            except Exception as e:
                logger.error(f"Reconnection failed: {e}")
                self.reconnect_count += 1
        
        logger.error("Max reconnection attempts reached")
        return False
    
    async def run(self):
        """Run WebSocket client with automatic reconnection."""
        while True:
            try:
                if not self.is_connected:
                    await self.connect()
                
                # Start ping task
                ping_task = asyncio.create_task(self._ping())
                
                # Handle messages
                await self._handle_messages()
                
                # Cancel ping task if message handling stops
                ping_task.cancel()
                
                # Attempt reconnection
                if not await self._reconnect():
                    break
                    
            except Exception as e:
                logger.error(f"WebSocket run error: {e}")
                if not await self._reconnect():
                    break
    
    async def subscribe_kline(self, symbol: str, interval: str):
        """
        Subscribe to kline/candlestick updates.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval ('1', '3', '5', '15', '30', '60', etc.)
        """
        topic = f"kline.{interval}.{symbol}"
        await self.subscribe([topic])
    
    async def subscribe_ticker(self, symbol: str):
        """
        Subscribe to ticker updates.
        
        Args:
            symbol: Trading pair symbol
        """
        topic = f"tickers.{symbol}"
        await self.subscribe([topic])
    
    async def subscribe_orderbook(self, symbol: str, depth: int = 50):
        """
        Subscribe to orderbook updates.
        
        Args:
            symbol: Trading pair symbol
            depth: Orderbook depth (1, 50, 200, 500)
        """
        topic = f"orderbook.{depth}.{symbol}"
        await self.subscribe([topic])
    
    async def subscribe_trades(self, symbol: str):
        """
        Subscribe to public trades.
        
        Args:
            symbol: Trading pair symbol
        """
        topic = f"publicTrade.{symbol}"
        await self.subscribe([topic])


class MarketDataManager:
    """Manager for market data from multiple WebSocket connections."""
    
    def __init__(self, testnet: bool = True):
        """
        Initialize market data manager.
        
        Args:
            testnet: Use testnet or mainnet
        """
        self.testnet = testnet
        self.ws_clients: Dict[str, BybitWebSocket] = {}
        self.data_cache: Dict[str, Any] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        
        logger.info("Market data manager initialized")
    
    async def _handle_message(self, data: Dict[str, Any]):
        """
        Handle incoming market data.
        
        Args:
            data: Market data message
        """
        topic = data.get('topic', '')
        data_type = topic.split('.')[0] if topic else ''
        
        # Cache the data
        self.data_cache[topic] = {
            'data': data.get('data'),
            'timestamp': datetime.now()
        }
        
        # Call registered callbacks
        if data_type in self.callbacks:
            for callback in self.callbacks[data_type]:
                try:
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error in callback for {data_type}: {e}")
    
    def register_callback(self, data_type: str, callback: Callable):
        """
        Register callback for specific data type.
        
        Args:
            data_type: Data type ('kline', 'tickers', 'orderbook', 'publicTrade')
            callback: Callback function
        """
        if data_type not in self.callbacks:
            self.callbacks[data_type] = []
        self.callbacks[data_type].append(callback)
        logger.info(f"Callback registered for {data_type}")
    
    async def subscribe_klines(self, symbols: List[str], intervals: List[str]):
        """
        Subscribe to klines for multiple symbols and intervals.
        
        Args:
            symbols: List of trading pair symbols
            intervals: List of kline intervals
        """
        ws = BybitWebSocket(testnet=self.testnet, on_message=self._handle_message)
        
        topics = []
        for symbol in symbols:
            for interval in intervals:
                topics.append(f"kline.{interval}.{symbol}")
        
        self.ws_clients['kline'] = ws
        
        # Start WebSocket in background
        asyncio.create_task(ws.run())
        
        # Wait for connection
        await asyncio.sleep(1)
        
        # Subscribe to topics
        await ws.subscribe(topics)
    
    def get_latest_kline(self, symbol: str, interval: str) -> Optional[Dict]:
        """
        Get latest kline data from cache.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval
            
        Returns:
            Latest kline data or None
        """
        topic = f"kline.{interval}.{symbol}"
        cached = self.data_cache.get(topic)
        
        return cached.get('data') if cached else None
    
    async def shutdown(self):
        """Shutdown all WebSocket connections."""
        for ws in self.ws_clients.values():
            await ws.disconnect()
        logger.info("All WebSocket connections closed")
